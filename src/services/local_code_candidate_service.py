"""Local-only candidate generation within a fixed pure-function edit boundary.

Candidates are data until the independently staged sandbox tests run. No model
can edit imports, class attributes, public signatures, tests, write services,
approval controls, credentials, or this updater.
"""
import ast
from src.ai.llm.inference_queue import service_class
from dataclasses import dataclass, field
import json
import textwrap
from pathlib import Path

from src.services.document_processor_training_contracts import BEHAVIOR_CODES
from src.services.local_correction_memory_service import ApprovedDocumentLessons


TARGETS = {
    "correct_filename": "src/services/filename_policy_service.py",
    "correct_authorization_filename_subtype": "src/services/filename_policy_service.py",
    "remove_false_review_reason": "src/services/review_reason_summary_service.py",
    "add_required_review_reason": "src/services/review_reason_summary_service.py",
}
DENIED = frozenset({
    "eval","exec","compile","open","input","globals","locals","vars","dir",
    "getattr","setattr","delattr","__import__","breakpoint","exit","quit",
    "system","popen","spawn","fork","unlink","remove","write","write_text",
    "write_bytes","read_text","read_bytes","socket","connect","request",
    "requests","subprocess","importlib","os","sys","ctypes",
})


@dataclass(frozen=True, repr=False)
class LocalCodeCandidate:
    path: str
    before: str = field(repr=False)
    after: str = field(repr=False)
    changed_function: str


def _methods(tree):
    return {
        cls.name+"."+function.name: function
        for cls in tree.body if isinstance(cls, ast.ClassDef)
        for function in cls.body if isinstance(function, ast.FunctionDef)
        if not function.name.startswith("__")
    }


def validate_candidate(before, after, selected):
    """Require exactly one existing method body to change, no new capabilities."""
    if not isinstance(after,str) or len(after)>100000:
        raise ValueError("local_candidate_invalid")
    old,new=ast.parse(before),ast.parse(after)
    old_methods,new_methods=_methods(old),_methods(new)
    if selected not in old_methods or set(old_methods)!=set(new_methods):
        raise ValueError("local_candidate_scope_invalid")
    old_method,new_method=old_methods[selected],new_methods[selected]
    if ast.dump(old_method.args)!=ast.dump(new_method.args):
        raise ValueError("local_candidate_interface_changed")
    # Replace only the candidate method body for a full structural equality test.
    candidate_body=new_method.body
    new_method.body=old_method.body
    if ast.dump(old)!=ast.dump(new):
        raise ValueError("local_candidate_outside_body")
    new_method.body=candidate_body
    old_strings={n.value for n in ast.walk(old) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
    old_calls={ast.dump(n.func) for n in ast.walk(old_method) if isinstance(n,ast.Call)}
    for node in ast.walk(new_method):
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.Lambda,
                            ast.AsyncFunctionDef,ast.Yield,ast.YieldFrom)):
            raise ValueError("local_candidate_capability_denied")
        if isinstance(node,ast.Name) and (node.id in DENIED or node.id.startswith("__")):
            raise ValueError("local_candidate_capability_denied")
        if isinstance(node,ast.Attribute) and (node.attr in DENIED or node.attr.startswith("__")):
            raise ValueError("local_candidate_capability_denied")
        if isinstance(node,ast.Call) and ast.dump(node.func) not in old_calls:
            raise ValueError("local_candidate_new_call_denied")
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value not in old_strings:
            raise ValueError("local_candidate_new_literal_denied")
    if ast.dump(old_method)==ast.dump(new_method):
        raise ValueError("local_candidate_no_change")
    return True


class LocalCodeCandidateService:
    def __init__(self, *, provider=None):
        self.provider=provider

    @service_class('training')
    def propose(self, *, root, family, code):
        family=ApprovedDocumentLessons.family(family)
        if family is None or code not in TARGETS:
            raise ValueError("local_code_scope_unavailable")
        relative=TARGETS[code]
        path=Path(root)/relative
        before=path.read_text(encoding="utf-8-sig")
        methods=_methods(ast.parse(before))
        schema={"type":"object","additionalProperties":False,
                "properties":{"action":{"type":"string","enum":["no_change","replace_method"]},
                    "method":{"type":"string","enum":list(methods)},
                    "body":{"type":"string"}},
                "required":["action","method","body"]}
        if self.provider is None:
            from src.ai.llm.providers.ollama_provider import OllamaProvider
            self.provider=OllamaProvider()
        result=self.provider._chat(
            system_prompt=(
                "You maintain the local LTHHC document processor. Resolution was approved. "
                "Review the existing implementation against the fixed approved behavior. "
                "Return no_change unless a necessary general correction is supported. "
                "Only replace one existing method body. Preserve signatures, decorators, "
                "imports and every other method. No new calls or string literals. Never "
                "weaken evidence validation, infer values, or change human ownership. "
                "Body must be Python statements without the def line. No tools or network."
            ),
            user_prompt=json.dumps({"document_family":family,
                "approved_behavior":BEHAVIOR_CODES[code],"module":before}),
            schema=schema,seed=self.provider.seed,
        )
        if not isinstance(result,dict) or set(result)!={"action","method","body"}:
            raise ValueError("local_candidate_response_invalid")
        if result["action"]=="no_change":
            return None
        selected=result["method"]
        if result["action"]!="replace_method" or selected not in methods or not isinstance(result["body"],str):
            raise ValueError("local_candidate_response_invalid")
        method=methods[selected]
        statements=ast.parse(result["body"]).body
        if not statements:
            raise ValueError("local_candidate_invalid")
        # Build candidate as text without compiling/importing/executing it on host.
        lines=before.splitlines(keepends=True)
        body="\n".join(ast.unparse(item) for item in statements)+"\n"
        after=("".join(lines[:method.body[0].lineno-1])
               +textwrap.indent(body," "*(method.col_offset+4))
               +"".join(lines[method.end_lineno:]))
        validate_candidate(before,after,selected)
        return LocalCodeCandidate(relative,before,after,selected)

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


EXPECTED = {
    "LTHHC AI Platform": "In Progress",
    "Design Security Model": "In Progress",
    "Install PaddleOCR": "Completed",
    "Extract Image Text": "Completed",
    "Handle Low Confidence": "Completed",
    "Install Base Model": "Completed",
    "Handle Retry Logic": "Completed",
    "Benchmark Performance": "In Progress",
    "Create Rules Engine": "Completed",
    "Validate Required Fields": "Completed",
    "Normalize Values": "Completed",
    "Generate Exceptions": "Completed",
    "Handle API Errors": "Completed",
    "System Testing": "In Progress",
    "Performance Testing": "In Progress",
    "Production Deployment": "In Progress",
}


def tracker_updates():
    tree = ast.parse(
        (ROOT / "update_project_tracker.py").read_text(encoding="utf-8-sig")
    )
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "updates" for target in node.targets)
    )
    return {name: status for name, status, _ in ast.literal_eval(assignment.value)}


def test_reconciled_tasks_use_exact_evidence_supported_statuses():
    updates = tracker_updates()
    for name, status in EXPECTED.items():
        assert updates.get(name) == status


def test_uncertain_tasks_are_not_newly_forced_to_completion():
    updates = tracker_updates()
    for name in (
        "Define Success Criteria",
        "Approve Requirements",
        "Review Architecture",
        "Approve Architecture",
        "Benchmark OCR Accuracy",
        "User Acceptance Testing",
        "Go Live",
        "Hypercare",
    ):
        assert updates.get(name) != "Completed"


def test_durable_tracker_rule_and_single_next_start_exist():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8-sig")
    memory = (ROOT / "PROJECT_MEMORY.md").read_text(encoding="utf-8-sig")
    assert "reconcile affected tracked WBS/task rows" in agents
    assert "never infer completion without evidence" in agents.lower()
    assert memory.count("## CURRENT NEXT START") == 1


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic repository-text validation")
    print("External integration: not called")
    print("PHI handling: task names and repository rules only")

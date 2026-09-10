"""Shared local-only Ollama wire contract. No program prompts or business context."""
import json
import os
from typing import Any
import requests


class LocalOllamaTransport:
    CHAT_ENDPOINT = "/api/chat"
    CONTEXT_CONTRACT_VERSION = 1
    VERIFIED_CONTEXT_API_VERSIONS = frozenset({"0.33.3"})
    SAFE_METRIC_FIELDS = ("done", "done_reason", "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration")

    @staticmethod
    def _positive_token_setting(name: str, default: int) -> int:
        raw = os.getenv(name, str(default))
        if (not isinstance(raw, str) or len(raw) > 10 or not raw.isascii()
                or not raw.isdecimal() or int(raw) <= 0):
            raise RuntimeError("local_model_context_configuration_invalid")
        return int(raw)


    def _verify_local_inference_target(self) -> dict:
        from urllib.parse import urlsplit
        target = urlsplit(self.base_url)
        if (target.scheme != "http" or target.hostname not in {"localhost", "127.0.0.1", "::1"}
                or target.username or target.password or target.query or target.fragment
                or target.path not in {"", "/"}):
            raise RuntimeError("local_model_endpoint_required")
        try:
            # Metadata only, before any protected prompt. Cloud aliases are rejected
            # even when the Ollama HTTP server itself is on localhost.
            response = requests.post(
                self.base_url + "/api/show", json={"model": self.model},
                timeout=self.timeout, allow_redirects=False,
                proxies={"http": "", "https": ""},
            )
            if response.status_code != 200:
                raise ValueError()
            data = response.json()
            if (not isinstance(data, dict) or data.get("remote_host") or data.get("remote_model")
                    or not isinstance(data.get("model_info"), dict) or not data["model_info"]):
                raise ValueError()
        except Exception:
            raise RuntimeError("local_model_identity_unproven") from None
        return data["model_info"]


    def _verify_context_contract(self, model_info: dict) -> tuple[int, int]:
        context = self.context_tokens
        output = self.max_output_tokens
        capacities = [v for k, v in model_info.items()
                      if k.endswith(".context_length") and type(v) is int and v > 0]
        if (type(context) is not int or type(output) is not int or not capacities
                or not 0 < output <= context <= min(capacities)):
            raise RuntimeError("local_model_context_configuration_invalid")
        try:
            response = requests.get(
                self.base_url + "/api/version", timeout=min(self.timeout, 10),
                allow_redirects=False, proxies={"http":"", "https":""})
            version = response.json().get("version") if response.status_code == 200 else None
        except Exception:
            raise RuntimeError("local_model_context_contract_unproven") from None
        # Old servers can silently ignore unknown request keys. Do not send a
        # protected prompt unless the no-truncate/no-shift API is verified.
        if not isinstance(version, str) or version not in self.VERIFIED_CONTEXT_API_VERSIONS:
            raise RuntimeError("local_model_context_contract_unproven")
        return context, output


    def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        seed: int,
    ) -> dict:
        self._last_request_metrics = {}
        model_info = self._verify_local_inference_target()
        context_tokens, max_output_tokens = self._verify_context_contract(model_info)
        endpoint = (
            f"{self.base_url}"
            f"{self.CHAT_ENDPOINT}"
        )

        self._last_request_metrics = {}

        payload = {
            "model": self.model,
            "stream": False,
            "truncate": False,
            "shift": False,
            "format": schema,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0,
                "seed": seed,
                "num_ctx": context_tokens,
                "num_predict": max_output_tokens,
            },
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout,
                allow_redirects=False,
                proxies={"http": "", "https": ""},
            )

            response.raise_for_status()

        except requests.ConnectionError:
            raise RuntimeError("local_model_unavailable") from None

        except requests.Timeout:
            raise RuntimeError("local_model_request_timeout") from None

        except requests.HTTPError:
            raise RuntimeError("local_model_http_error") from None

        except requests.RequestException:
            raise RuntimeError("local_model_request_failed") from None

        try:
            response_payload = response.json()
        except ValueError as ex:
            raise RuntimeError(
                "Ollama returned a response that was not valid JSON."
            ) from ex

        if not isinstance(
            response_payload,
            dict,
        ):
            raise RuntimeError(
                "Ollama response payload must be a JSON object."
            )

        self._last_request_metrics = self._extract_safe_metrics(
            response_payload
        )
        self._last_request_metrics.update(
            context_contract_version=self.CONTEXT_CONTRACT_VERSION,
            requested_context_tokens=context_tokens,
            maximum_output_tokens=max_output_tokens,
            input_truncation_allowed=False,
            context_shift_allowed=False,
        )
        if response_payload.get("done") is not True or response_payload.get("done_reason") != "stop":
            raise RuntimeError("local_model_response_incomplete") from None

        message = response_payload.get(
            "message"
        )

        if not isinstance(
            message,
            dict,
        ):
            raise RuntimeError(
                "Ollama response did not contain a message object."
            )

        content = message.get(
            "content"
        )

        if (
            not isinstance(
                content,
                str,
            )
            or not content.strip()
        ):
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        try:
            parsed_content = json.loads(
                content
            )
        except json.JSONDecodeError as ex:
            raise RuntimeError(
                "Ollama returned content that was not valid "
                "structured JSON."
            ) from ex

        if not isinstance(
            parsed_content,
            dict,
        ):
            raise RuntimeError(
                "Ollama structured output must be a JSON object."
            )

        return parsed_content


    def _extract_safe_metrics(
        self,
        response_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract only PHI-safe timing and generation metadata.
        """

        metrics: dict[str, Any] = {}

        for field_name in self.SAFE_METRIC_FIELDS:
            value = response_payload.get(
                field_name
            )

            if ((field_name == "done" and type(value) is bool)
                    or (field_name == "done_reason" and isinstance(value, str)
                        and value in {"stop", "length"})
                    or (field_name not in {"done", "done_reason"}
                        and type(value) in (int, float) and 0 <= value < float("inf"))):
                metrics[field_name] = value

        for duration_field in (
            "total_duration",
            "load_duration",
            "prompt_eval_duration",
            "eval_duration",
        ):
            duration_value = metrics.get(
                duration_field
            )

            if isinstance(
                duration_value,
                (
                    int,
                    float,
                ),
            ):
                metrics[
                    f"{duration_field}_seconds"
                ] = (
                    float(
                        duration_value
                    )
                    / 1_000_000_000
                )

        eval_count = metrics.get(
            "eval_count"
        )

        eval_duration_seconds = metrics.get(
            "eval_duration_seconds"
        )

        if (
            isinstance(
                eval_count,
                int,
            )
            and eval_count >= 0
            and isinstance(
                eval_duration_seconds,
                float,
            )
            and eval_duration_seconds > 0
        ):
            metrics[
                "generation_tokens_per_second"
            ] = (
                eval_count
                / eval_duration_seconds
            )

        return metrics

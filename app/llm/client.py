import json
import urllib.error
import urllib.request
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class FakeLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "JSON" in system_prompt and "extract" in system_prompt.lower():
            return self._mock_extraction(user_prompt)

        lines = [line.strip() for line in user_prompt.splitlines() if line.strip()]
        context_lines = [
            line for line in lines
            if line.startswith("[source:") or line.startswith("[citation:")
        ]
        if not context_lines:
            return "The answer cannot be determined from the available documents."
        return "Based on the retrieved context: " + context_lines[0]

    def _mock_extraction(self, text: str) -> str:
        mock = {
            "trial_id": "trial_adc_001",
            "phase": "Phase II",
            "indication": "HER2-positive solid tumors",
            "intervention": "ADC-101",
            "primary_endpoint": "Objective response rate",
            "secondary_endpoints": ["Progression-free survival", "Safety"],
            "sample_size": 120,
            "inclusion_criteria": ["Adult patients", "ECOG performance status 0-1"],
            "exclusion_criteria": ["Uncontrolled infection"],
        }
        return json.dumps(mock)


class OpenAICompatibleClient:
    """Client for any OpenAI-compatible chat completion API.

    Supports OpenAI, DeepSeek, Qwen, SiliconFlow, OpenRouter, local vLLM,
    Ollama (with OpenAI-compatible adapter), and other providers that expose
    a ``/v1/chat/completions`` endpoint.

    Text-only. Does not support multimodal, image, PDF, OCR, or streaming.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                response_body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            status = e.code
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM API error (HTTP {status}): {self._safe_detail(detail)}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"LLM API connection failed: {e.reason}"
            ) from e
        except TimeoutError as e:
            raise RuntimeError("LLM API request timed out") from e

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"LLM API returned invalid JSON: {response_body[:200]}"
            ) from e

        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("content is not a string")
            return content
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(
                f"LLM API response missing content field: {json.dumps(data)[:200]}"
            ) from e

    def _safe_detail(self, detail: str) -> str:
        if self.api_key:
            detail = detail.replace(self.api_key, "[redacted]")
        return detail[:200]

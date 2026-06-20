from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class FakeLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        lines = [line.strip() for line in user_prompt.splitlines() if line.strip()]
        context_lines = [line for line in lines if line.startswith("[source:")]
        if not context_lines:
            return "The answer cannot be determined from the available documents."
        return "Based on the retrieved context: " + context_lines[0]

import json
import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.core.container import create_llm_client
from app.llm.client import FakeLLMClient, OpenAICompatibleClient


class TestDefaultFake:
    def test_fake_is_returned_by_default(self) -> None:
        cfg = Settings(_env_file=None)
        client = create_llm_client(cfg)
        assert isinstance(client, FakeLLMClient)

    def test_fake_generate_works(self) -> None:
        cfg = Settings(llm_provider="fake", _env_file=None)
        client = create_llm_client(cfg)
        answer = client.generate("system", "Question: test\n\nContext:\n[source:x] data")
        assert "Based on the retrieved context" in answer


class TestMissingKey:
    def test_raises_value_error_when_key_missing(self) -> None:
        cfg = Settings(llm_provider="openai-compatible", llm_api_key="", _env_file=None)
        with pytest.raises(ValueError, match="LLM_API_KEY is required"):
            create_llm_client(cfg)


class TestOpenAICompatibleFactory:
    def test_returns_openai_compatible_client_when_configured(self) -> None:
        cfg = Settings(
            llm_provider="openai-compatible",
            llm_api_key="sk-test",
            llm_base_url="https://api.openai.com/v1",
            llm_model="gpt-4o-mini",
            _env_file=None,
        )
        client = create_llm_client(cfg)
        assert isinstance(client, OpenAICompatibleClient)
        assert client.api_key == "sk-test"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.model == "gpt-4o-mini"

    def test_strips_trailing_slash_from_base_url(self) -> None:
        cfg = Settings(
            llm_provider="openai-compatible",
            llm_api_key="sk-test",
            llm_base_url="https://api.example.com/v1/",
            _env_file=None,
        )
        client = create_llm_client(cfg)
        assert client.base_url == "https://api.example.com/v1"


class TestOpenAICompatibleGenerate:
    def test_sends_correct_request_and_parses_response(self) -> None:
        mock_response = {
            "choices": [{"message": {"content": "The answer is 42."}}]
        }
        mock_body = json.dumps(mock_response).encode("utf-8")

        def fake_urlopen(request, **kwargs):
            # Verify request shape
            assert request.get_method() == "POST"
            assert request.headers.get("Content-type") == "application/json"
            assert request.headers.get("Authorization") == "Bearer sk-test"
            sent = json.loads(request.data)
            assert sent["model"] == "gpt-4o-mini"
            assert sent["messages"][0]["role"] == "system"
            assert sent["messages"][1]["role"] == "user"
            return FakeResponse(mock_body, 200)

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            result = client.generate("system prompt", "user prompt")
            assert result == "The answer is 42."

    def test_raises_on_api_error(self) -> None:
        def fake_urlopen(request, **kwargs):
            raise urllib.error.HTTPError(
                url="http://example.com",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=BytesIO(b'{"error":"unauthorized"}'),
            )

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="LLM API error.*401"):
                client.generate("system", "user")

    def test_redacts_api_key_from_api_error(self) -> None:
        def fake_urlopen(request, **kwargs):
            raise urllib.error.HTTPError(
                url="http://example.com",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=BytesIO(b'{"error":"invalid key sk-secret"}'),
            )

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-secret")
            with pytest.raises(RuntimeError) as exc:
                client.generate("system", "user")
            assert "sk-secret" not in str(exc.value)
            assert "[redacted]" in str(exc.value)

    def test_raises_on_connection_error(self) -> None:
        def fake_urlopen(request, **kwargs):
            raise urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="LLM API connection failed"):
                client.generate("system", "user")

    def test_raises_on_invalid_json(self) -> None:
        def fake_urlopen(request, **kwargs):
            return FakeResponse(b"not json", 200)

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="invalid JSON"):
                client.generate("system", "user")

    def test_raises_on_missing_content_field(self) -> None:
        mock_response = {"choices": [{"message": {}}]}

        def fake_urlopen(request, **kwargs):
            return FakeResponse(json.dumps(mock_response).encode("utf-8"), 200)

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="missing content"):
                client.generate("system", "user")

    def test_raises_on_empty_choices(self) -> None:
        mock_response = {"choices": []}

        def fake_urlopen(request, **kwargs):
            return FakeResponse(json.dumps(mock_response).encode("utf-8"), 200)

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="missing content"):
                client.generate("system", "user")

    def test_raises_on_non_string_content(self) -> None:
        mock_response = {"choices": [{"message": {"content": None}}]}

        def fake_urlopen(request, **kwargs):
            return FakeResponse(json.dumps(mock_response).encode("utf-8"), 200)

        with patch("urllib.request.urlopen", fake_urlopen):
            client = OpenAICompatibleClient(api_key="sk-test")
            with pytest.raises(RuntimeError, match="missing content"):
                client.generate("system", "user")


class FakeResponse:
    """Minimal stand-in for http.client.HTTPResponse."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        pass

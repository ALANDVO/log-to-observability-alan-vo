import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm_advisor import LLMAdvisor

@pytest.mark.asyncio
async def test_offline_mode_when_no_api_key():
    advisor = LLMAdvisor()
    advisor.api_key = ""
    advisor.provider = "openai-compatible"

    res = await advisor.generate_advisory("Review architecture")
    assert "Offline deterministic mode active" in res

@pytest.mark.asyncio
async def test_llm_redaction_and_openai_mock():
    synthetic_key = "dummy-" + "0" * 32
    advisor = LLMAdvisor()
    advisor.api_key = synthetic_key
    advisor.provider = "openai-compatible"

    # Verify redaction method
    redacted = advisor._redact(f"Error communicating with key {synthetic_key}")
    assert synthetic_key not in redacted
    assert "[REDACTED]" in redacted

    # Test mocked API call
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Architecture looks resilient."}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        output = await advisor.generate_advisory("Test prompt")
        assert output == "Architecture looks resilient."

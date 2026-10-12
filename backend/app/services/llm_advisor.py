import re
import json
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class LLMAdvisor:
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.provider = settings.llm_provider.lower()
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url.rstrip("/")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) or self.provider == "ollama"

    async def generate_advisory(self, prompt: str, system_prompt: str = "You are an SRE advisory expert.") -> str:
        """Call configured LLM provider with strict timeout and redacted error handling."""
        if not self.is_configured:
            return (
                "Advisory: Offline deterministic mode active. LLM advisory is opt-in and disabled "
                "because no LLM_API_KEY is configured. All topology, alerts, and dashboards are computed deterministically."
            )

        timeout = httpx.Timeout(30.0, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self.provider == "anthropic":
                    return await self._call_anthropic(client, prompt, system_prompt)
                elif self.provider == "gemini":
                    return await self._call_gemini(client, prompt, system_prompt)
                elif self.provider == "ollama":
                    return await self._call_ollama(client, prompt, system_prompt)
                else:
                    # Default: openai-compatible
                    return await self._call_openai(client, prompt, system_prompt)
        except httpx.TimeoutException:
            return "Advisory Provider Error: Request timed out after 30 seconds."
        except Exception as e:
            # Redact any accidental credential leak
            safe_err = self._redact(str(e))
            return f"Advisory Provider Error: {safe_err}"

    async def _call_openai(self, client: httpx.AsyncClient, prompt: str, system: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, client: httpx.AsyncClient, prompt: str, system: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        url = f"{self.base_url}/messages" if "messages" in self.base_url else f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["content"][0]["text"]

    async def _call_gemini(self, client: httpx.AsyncClient, prompt: str, system: str) -> str:
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
        }
        res = await client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_ollama(self, client: httpx.AsyncClient, prompt: str, system: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        res = await client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["message"]["content"]

    def _redact(self, message: str) -> str:
        if self.api_key and len(self.api_key) > 4:
            message = message.replace(self.api_key, "[REDACTED]")
        # Regex redaction for token patterns
        message = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [REDACTED]', message)
        return message

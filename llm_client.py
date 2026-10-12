"""Unified LLM client interface."""
import sys
import os
import asyncio

backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.llm_advisor import LLMAdvisor

class LLM:
    def __init__(self):
        self._advisor = LLMAdvisor()

    def generate(self, prompt: str, system: str = "You are a helpful AI assistant.") -> str:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self._advisor.generate_advisory(prompt, system_prompt=system))
        return asyncio.run(self._advisor.generate_advisory(prompt, system_prompt=system))

    def chat(self, messages, temperature=0.7, max_tokens=2048):
        user_msg = messages[-1]["content"] if messages else ""
        sys_msg = messages[0]["content"] if len(messages) > 1 and messages[0]["role"] == "system" else ""
        return self.generate(user_msg, system=sys_msg)

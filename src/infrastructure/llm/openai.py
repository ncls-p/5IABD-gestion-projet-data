import requests
from typing import List
from ...core.config import get_settings
from ...domain.interfaces.repositories import LLMRepository
from ...core.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class OpenAIRepository(LLMRepository):
    def __init__(self):
        self.api_url = settings.LLM_API_URL
        self.api_key = settings.LLM_API_KEY
        self.model_id = settings.MODEL_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: List[dict], functions: List[dict]) -> dict:
        payload = {
            "model": self.model_id,
            "messages": messages,
            "functions": functions,
            "function_call": "auto",
            "stream": False,
        }

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=300,
        )
        return response.json()

    async def generate_ics(self, messages: List[dict]) -> str:
        calendar_prompt = {
            "role": "user",
            "content": "Convert the above chat into an ICS calendar format. Respond ONLY with the ICS content, no markdown.",
        }
        messages = messages + [calendar_prompt]

        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
        }

        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=300,
        )

        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        return ""

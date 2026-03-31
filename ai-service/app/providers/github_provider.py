import httpx
from app.providers.base import LLMProvider


class GitHubModelsProvider(LLMProvider):
    BASE_URL = "https://models.inference.ai.azure.com/chat/completions"

    def __init__(self, token: str, model: str):
        self.token = token
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def get_name(self) -> str:
        return "GitHubModels"

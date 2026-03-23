import requests
import json
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> str:
        """Takes a prompt and returns a JSON string response."""
        pass

class LocalLLMClient(BaseLLMClient):
    """
    Client for interacting with local LLMs via endpoints like Ollama.
    Expects an endpoint supporting the `/api/generate` schema.
    """
    def __init__(self, endpoint: str, model: str, temperature: float = 0.0, max_tokens: int = 32):
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_json(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": self.temperature,
            "options": {
                "num_predict": self.max_tokens
            },
            # Ollama specific format flag to ensure JSON
            "format": "json"
        }
        
        try:
            response = requests.post(self.endpoint, json=payload,timeout=20)
            response.raise_for_status()
            response_data = response.json()
            # The `/api/generate` endpoint typically returns `response` field
            text_resp = response_data.get("response", "")
            return text_resp
        except Exception as e:
            print(f"[LocalLLMClient] Error generating response from {self.endpoint}: {e}")
            raise

# Agents/client.py
from openai import AzureOpenAI
import os

class AzureOpenAIClient:
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("API_VERSION", "2025-02-01-preview")
        self.deployment_name = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
        
        self._validate_config()
        self.client = self._create_client()

    def _validate_config(self):
        required = [
            ("AZURE_ENDPOINT", self.azure_endpoint),
            ("AZURE_OPENAI_API_KEY", self.api_key)
        ]
        for name, value in required:
            if not value:
                raise ValueError(f"{name} not set in .env")

    def _create_client(self):
        return AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )

    def chat_completion(self, messages, temperature=0.4, max_tokens=1000):
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
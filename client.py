from openai import AzureOpenAI
import os

class AzureOpenAIClient:
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.deployment_name = os.getenv("DEPLOYMENT_NAME")
        
        self._validate_config()
        
        self.client = self._create_client()

    def _validate_config(self):
        required_configs = [
            ("AZURE_ENDPOINT", self.azure_endpoint),
            ("AZURE_API_KEY", self.api_key),
            ("AZURE_API_VERSION", self.api_version),
            ("DEPLOYMENT_NAME", self.deployment_name)
        ]
        for config_name, config_value in required_configs:
            if not config_value:
                raise ValueError(f"配置项 {config_name} 未设置，请检查config.sh")

    def _create_client(self):
        return AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )

    def chat_completion(self, messages, temperature=0.4, max_tokens=1000, stream=False):
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        return response.choices[0].message.content
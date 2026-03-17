# Agents/BaseAgent.py
import os
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Get project root (parent of Agents folder)
project_root = Path(__file__).parent.parent

# Load .env file from project root
load_dotenv(project_root / '.env')

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, client=None, model=None):
        from openai import AzureOpenAI
        
        self.client = client or AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2025-02-01-preview")
        )
        self.model = model or os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
        self.history: List[Dict[str, str]] = []
    
    def resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute path relative to project root"""
        if os.path.isabs(path):
            return Path(path)
        return project_root / path
    
    def load_prompt_file(self, prompt_path: str) -> str:
        """Load prompt from file, automatically handle relative paths"""
        full_path = self.resolve_path(prompt_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Error: Prompt file not found: {full_path}")
            return ""
    
    def set_system_prompt(self, prompt: str):
        """Set or update system prompt"""
        # Remove old system prompt if exists
        self.history = [msg for msg in self.history if msg["role"] != "system"]
        # Add new system prompt at beginning
        self.history.insert(0, {"role": "system", "content": prompt})
    
    def add_message(self, role: str, content: str):
        """Add a message to history"""
        self.history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Clear all messages except system prompt"""
        system_msgs = [msg for msg in self.history if msg["role"] == "system"]
        self.history = system_msgs
    
    def call(self, messages: List[Dict[str, str]], temperature: float = 0.4, max_tokens: int = 1000) -> str:
        """Make API call with given messages"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Main method to be implemented by subclasses"""
        pass
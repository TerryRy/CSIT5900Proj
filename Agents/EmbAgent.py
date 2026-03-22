import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from Agents.BaseAgent import BaseAgent
from .embedder import Embedder

class EmbAgent(BaseAgent):
    """Embedding-based agent that checks relevance before answering"""
    
    def __init__(self, client=None, model=None):
        super().__init__(client, model)
        
        # Initialize relevance checker
        self.relevance_checker = Embedder(
            model_name="BAAI/bge-m3",
            domain_threshold=0.55,
            summary_threshold=0.4,
            continuation_threshold=0.1
        )
        
        # Load system prompt from environment variable
        prompt_path = os.getenv("SYSTEM_PROMPT_PATH", "./templates/basic_prompts/few_shot.txt")
        self.system_prompt = self.load_prompt_file(prompt_path)
        self.set_system_prompt(self.system_prompt)
    
    def load_prompt(self, prompt_path: str):
        """Load prompt from file (compatibility method)"""
        prompt = self.load_prompt_file(prompt_path)
        if prompt:
            self.system_prompt = prompt
            self.set_system_prompt(prompt)
    
    def chat(self, message: str, history: List[Tuple[str, str]]) -> str:
        """Chat method for Gradio interface"""
        # Check relevance
        if not self.relevance_checker.is_relevant(message, history):
            return "Sorry, this SmartTutor only answers math and world history homework questions for college and below. Please ask relevant questions."
        
        # Build messages from history
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for user_msg, ai_msg in history:
            messages.append({"role": "user", "content": user_msg})
            if ai_msg:
                messages.append({"role": "assistant", "content": ai_msg})
        
        messages.append({"role": "user", "content": message})
        
        # Call API
        response = self.call(messages, temperature=0.4, max_tokens=1000)
        return response
    
    def run(self, input_data: Any) -> Any:
        """Main method required by BaseAgent"""
        # input_data can be a tuple of (message, history) or just message
        if isinstance(input_data, tuple) and len(input_data) == 2:
            message, history = input_data
        else:
            message = input_data
            history = []
        
        return self.chat(message, history)
    
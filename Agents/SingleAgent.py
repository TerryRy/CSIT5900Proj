# Agents/Agent.py
from typing import List, Tuple
from .BaseAgent import BaseAgent

class SmartTutor(BaseAgent):
    """Single Agent - SmartTutor"""
    
    def __init__(self, client=None, model=None):
        super().__init__(client, model)
        self.system_prompt = None
    
    def load_prompt(self, prompt_path: str):
        self.system_prompt = self.load_prompt_file(prompt_path)
        self.set_system_prompt(self.system_prompt)
    
    def chat(self, message: str, history: List[Tuple[str, str]] = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if history:
            for user_msg, ai_msg in history:
                messages.append({"role": "user", "content": user_msg})
                if ai_msg:
                    messages.append({"role": "assistant", "content": ai_msg})
        
        messages.append({"role": "user", "content": message})
        
        response = self.call(messages)
        
        self.add_message("user", message)
        self.add_message("assistant", response)
        
        # TODO: 注释掉以下if语句即可
        if response.startswith("Error: Error code: 400 - {'error': {'message'"):
            response = "Sorry I cannot help you on that as this question includes security issues, please follow the security policy when asking questions."
        
        return response
    
    def reset_history(self):
        """Reset conversation history"""
        self.history = [{"role": "system", "content": self.system_prompt}]
    
    def run(self, input_data: dict) -> str:
        message = input_data.get("message", "")
        history = input_data.get("history", [])
        return self.chat(message, history)
# Agents/TwoAgents.py
import json
from typing import List, Tuple, Dict, Any, Optional
from .BaseAgent import BaseAgent

class TutorAgent(BaseAgent):
    """Tutor Agent (A) - Answers questions"""
    
    def __init__(self, client=None, model=None):
        super().__init__(client, model)
        self.system_prompt = None
    
    def load_prompt(self, prompt_path: str):
        self.system_prompt = self.load_prompt_file(prompt_path)
        self.set_system_prompt(self.system_prompt)
    
    def answer(self, question: str, history: List[Tuple[str, str]] = None, correction_context: str = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if correction_context:
            messages.append({"role": "system", "content": f"Previous answer had issues: {correction_context}. Please provide a corrected answer."})
        
        if history:
            for user_msg, ai_msg in history:
                messages.append({"role": "user", "content": user_msg})
                if ai_msg:
                    messages.append({"role": "assistant", "content": ai_msg})
        
        messages.append({"role": "user", "content": question})
        
        response = self.call(messages)
        self.add_message("user", question)
        self.add_message("assistant", response)
        return response
    
    # 实现抽象方法
    def run(self, input_data: Dict[str, Any]) -> str:
        question = input_data.get("question", "")
        history = input_data.get("history", [])
        correction_context = input_data.get("correction_context", None)
        return self.answer(question, history, correction_context)


class CorrectorAgent(BaseAgent):
    """Corrector Agent (B) - Reviews answers and suggests improvements"""
    
    def __init__(self, client=None, model=None):
        super().__init__(client, model)
        self.system_prompt = None
    
    def load_prompt(self, prompt_path: str):
        self.system_prompt = self.load_prompt_file(prompt_path)
        self.set_system_prompt(self.system_prompt)
    
    def review(self, question: str, response: str, expected_type: str = None) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Question: {question}\nResponse: {response}\nExpected type: {expected_type}"}
        ]
        
        result = self.call(messages, temperature=0.2, max_tokens=200)
        
        try:
            if result.startswith("```"):
                result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return {"needs_correction": False}
    
    # 实现抽象方法
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data.get("question", "")
        response = input_data.get("response", "")
        expected_type = input_data.get("expected_type", None)
        return self.review(question, response, expected_type)


class TwoAgentSystem:
    """Two-Agent System: Tutor + Corrector with auto-correction loop"""
    
    def __init__(self, tutor_prompt_path: str, corrector_prompt_path: str, max_rounds: int = 3):
        self.tutor = TutorAgent()
        self.corrector = CorrectorAgent()
        
        self.tutor.load_prompt(tutor_prompt_path)
        self.corrector.load_prompt(corrector_prompt_path)
        
        self.max_rounds = max_rounds
        self.history = []
        self.correction_history = []
    
    def run(self, question: str, expected_type: str = None) -> Dict[str, Any]:
        """Run both agents"""
        current_response = None
        correction_context = None
        rounds = []
        
        for round_num in range(self.max_rounds):
            # Tutor answers
            response = self.tutor.answer(question, self.history, correction_context)
            
            # Corrector reviews
            review = self.corrector.review(question, response, expected_type)
            
            round_data = {
                "round": round_num + 1,
                "response": response,
                "review": review
            }
            rounds.append(round_data)
            
            needs_correction = review.get("needs_correction", False)
            
            if not needs_correction:
                current_response = response
                break
            else:
                issues = review.get("issues", [])
                suggestion = review.get("suggestion", "")
                correction_context = f"Round {round_num + 1} issues: {', '.join(issues)}. Suggestion: {suggestion}"
                
                if round_num == self.max_rounds - 1:
                    current_response = response
        
        if current_response is None and rounds:
            current_response = rounds[-1]["response"]
        
        self.history.append((question, current_response))
        
        self.correction_history.append({
            "question": question,
            "expected_type": expected_type,
            "rounds": rounds,
            "final_response": current_response,
            "needed_correction": len(rounds) > 1
        })
        
        return {
            "question": question,
            "response": current_response,
            "rounds": rounds,
            "total_rounds": len(rounds),
            "needed_correction": len(rounds) > 1
        }
    
    def reset(self):
        """Reset conversation history"""
        self.history = []
        self.tutor.clear_history()
        self.corrector.clear_history()
    
    def get_correction_stats(self) -> Dict[str, Any]:
        total = len(self.correction_history)
        if total == 0:
            return {"total": 0}
        
        corrected = sum(1 for h in self.correction_history if h["needed_correction"])
        return {
            "total": total,
            "corrected": corrected,
            "correction_rate": corrected / total * 100
        }
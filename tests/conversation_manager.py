# toolFiles/conversation_manager.py
import tiktoken
from typing import List, Tuple, Optional

class ConversationManager:
    def __init__(self, max_history_tokens: int = 2000):
        self.max_history_tokens = max_history_tokens
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.last_topic = None
    
    def _count_tokens(self, text: str) -> int:
        """计算token数量"""
        return len(self.encoder.encode(text))
    
    def compress_history(self, history: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """压缩对话历史，避免超长"""
        if not history:
            return []
        
        total_tokens = 0
        compressed = []
        
        # 从最新的对话开始保留
        for user_msg, ai_msg in reversed(history):
            msg_tokens = self._count_tokens(user_msg) + self._count_tokens(ai_msg or "")
            if total_tokens + msg_tokens > self.max_history_tokens:
                compressed.insert(0, ("-----[System Prompt]-----", "Previous conversation truncated due to length."))
                break
            compressed.insert(0, (user_msg, ai_msg))
            total_tokens += msg_tokens
        
        return compressed
    
    def detect_follow_up(self, message: str) -> bool:
        """检测是否为追问"""
        follow_up_indicators = [
            "why", "how", "explain", "what about", "and then", 
            "can you elaborate", "tell me more", "举个例子", "为什么",
            "具体", "详细", "接着说", "然后呢", "接着说"
        ]
        msg_lower = message.lower()
        return any(indicator in msg_lower for indicator in follow_up_indicators)
    
    def update_topic(self, message: str, response: str):
        """更新最后话题（如果不是拒绝回答）"""
        if not any(phrase in response for phrase in [
            "Sorry I cannot help you", 
            "Sorry that is not likely",
            "not a homework question"
        ]):
            self.last_topic = message
    
    def get_context_prompt(self, message: str) -> Optional[str]:
        """如果需要，返回上下文提示"""
        if self.detect_follow_up(message) and self.last_topic:
            return f"Note: This is a follow-up question about: {self.last_topic}"
        return None
    
    def reset(self):
        """重置对话状态"""
        self.last_topic = None
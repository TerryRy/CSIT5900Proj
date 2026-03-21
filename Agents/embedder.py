import torch
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Optional


class Embedder:
    """
    查询相关性检查器：使用两个 embedding 原型判断是否允许回答
    - domain_prototype: 必须是数学/历史作业相关
    - continuation_prototype: 允许对已有话题的合理追问、解释、总结等
    """

    def __init__(
        self,
        model_name="BAAI/bge-m3",
        domain_threshold=0.62,
        summary_threshold=0.7,
        continuation_threshold=0.58,
        device=None
    ):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.embedder = SentenceTransformer(model_name, device=device)
        self.domain_threshold = domain_threshold
        self.summary_threshold = summary_threshold
        self.continuation_threshold = continuation_threshold

        # 两个核心原型句（可通过子类或属性修改）
        self.domain_prototype = (
            "This is a mathematics assignment question at the undergraduate level or below, or an assignment question related to world history events, figures, timelines, cause-and-effect analysis, and cultural background."
        )
        self.summary_prototype = (
            "This is a summarization-type question. For example, summarizing the above questions, summarizing the conversation so far, summarizing each question."
        )
        self.continuation_prototype = (
            "These are reasonable follow-up questions to the previously discussed mathematical or world history issues, including but not limited to: why it is so, more detailed explanations, the proof process, counterexamples, giving more examples, summarizing the previous content, comparing two methods, solving similar problems, clarifying a concept, asking to explain again, I cannot understand, how, etc."
        )

        # 预先计算 embedding（初始化时只算一次）
        self.domain_emb = self.embedder.encode(
            self.domain_prototype, normalize_embeddings=True
        )
        self.summary_emb = self.embedder.encode(
            self.summary_prototype, normalize_embeddings=True
        )
        self.continuation_emb = self.embedder.encode(
            self.continuation_prototype, normalize_embeddings=True
        )

    def is_relevant(
        self,
        message: str,
        history: List[Tuple[Optional[str], Optional[str]]],
        max_history_turns: int = 3
    ) -> bool:
        """
        判断当前消息是否应该被回答
        Args:
            message: 当前用户输入
            history: gradio 格式的历史 [(user_msg, ai_msg), ...]
            max_history_turns: 拼接历史时最多考虑最近几轮
        Returns:
            bool: 是否允许回答
        """
        query_emb = self.embedder.encode(message, normalize_embeddings=True)

        # 1. 计算与领域原型的相似度
        sim_domain = util.cos_sim(query_emb, self.domain_emb).item()
        
        sim_summary = util.cos_sim(query_emb, self.summary_emb).item()

        # 2. 如果有历史，对话延续相似度
        sim_continuation = 0.0
        if history:
            context_parts = []
            for user_msg, ai_msg in history[-max_history_turns:]:
                if user_msg:
                    context_parts.append(f"学生: {user_msg}")
                if ai_msg:
                    context_parts.append(f"导师: {ai_msg}")

            if context_parts:
                context_text = "\n".join(context_parts)
                context_emb = self.embedder.encode(context_text, normalize_embeddings=True)
                sim_continuation = util.cos_sim(query_emb, context_emb).item()

        # 3. 最终判断：任一维度达标即可通过
        return (
            sim_domain > self.domain_threshold or
            sim_summary > self.summary_threshold or
            sim_continuation > self.continuation_threshold
        )
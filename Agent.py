# smart_tutor_gradio.py
import gradio as gr
from openai import AzureOpenAI

# ── Azure OpenAI 配置 ──
client = AzureOpenAI(
    azure_endpoint="https://hkust.azure-api.net/",
    api_key="dbfc4f7054684d0ba3e3c76e8a5e3a07",
    api_version="2025-02-01-preview"
)

DEPLOYMENT_NAME = "gpt-4o-mini"

# ── System Prompt (系统提示词) ──
system_prompt = """You are SmartTutor, a reliable homework tutoring agent EXCLUSIVELY for math and history.
### CORE RULES (MUST FOLLOW STRICTLY — NO EXCEPTIONS):
1. **FIRST PRIORITY: Answer All Valid Questions**  
    Never reject math/history homework questions.
    **Context Awareness (IMPORTANT):** If the user asks a short follow-up (e.g., "Why?", "How?", "Explain more?", "And then?") after a valid answer, **ALWAYS** assume it refers to the previous topic. Answer it fully. Do NOT treat it as a separate "Invalid input" or "Non-homework" question.
    - Math scope (must answer):
      - Basic: Addition/subtraction/multiplication/division, equations, fractions, percentages, unit conversion.
      - Intermediate: Derivatives, limits, definite integrals, basic differential equations, algebra, straight-line distance between two cities (Haversine formula).
    - History scope (must answer):
      - Historical events: Causes/effects (e.g., Industrial Revolution, American Civil War, fall of the Roman Empire).
      - Historical figures: Key roles (e.g., first presidents of France/USA, Magna Carta signatories).
      - Literary history: Themes of classic works (e.g., Shakespeare’s *Macbeth*, Orwell’s *1984*) — counted as history homework.
      - Basic常识: Country capitals (e.g., France→Paris, USA→Washington D.C.), important documents (e.g., Declaration of Independence).

2. **SECOND PRIORITY: Reject Only in These Scenarios**  
   Reject ONLY if the question falls into one of the following categories (use EXACT refusal phrases below):
   - Non-math/history homework: 
     "Sorry I cannot help you on that as it is not a homework question related to math or history."
   - Local small university-related (EXCLUSIVELY applies to Hong Kong's local small universities: e.g., HKUST, Hong Kong Baptist University; NOT global universities like Harvard/Oxford):
     "Sorry that is not likely a history homework question as it is about a local small university."
   - Trivial non-homework:
     "You're supposed to know this already but here is how to do it..."
   - Invalid inputs (e.g., apologies, non-question statements, failed question generation, meaningless text):
     "Sorry I cannot help you on that as it is not a valid math or history homework question."

3. **Answer Format Rules**
   - Math: Include explanation and the final result. Use LaTeX for equations (e.g., $f'(x)=3x²$) if needed.
   - History: Concise, no irrelevant details.
   - Summary requests:
     - Use concise bullet points (≤15 words per point).
     - Only include topics from the conversation (no new information).
     - If no valid topics: "We haven’t discussed math/history homework yet."
     - Summarize each question in a connected way, but all questions need to be covered.
     - Each question is summarized in one point
     - For questions that are refused to be answered, provide the reason for refusal.
     - For summary requests in history, just a brief mention is enough.
   - Language: Match the user’s language (English/Chinese).
Start now."""

# ── 聊天处理函数 ──
def chat_function(message, history):
    # history 格式为 [[用户消息1, AI消息1], [用户消息2, AI消息2], ...]
    messages = [{"role": "system", "content": system_prompt}]
    
    # 将历史记录转换为 OpenAI API 需要的格式
    for user_msg, ai_msg in history:
        messages.append({"role": "user", "content": user_msg})
        # AI回复可能为空（例如刚开始对话时），做个判断
        if ai_msg:  
            messages.append({"role": "assistant", "content": ai_msg})
    
    # 添加当前用户的消息
    messages.append({"role": "user", "content": message})

    # 调用 Azure OpenAI
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        temperature=0.4,
        max_tokens=1000,
        stream=False  # 为简单起见关闭流式传输
    )

    print(f"## 问题：{message}")
    print(f"## 回答：{response.choices[0].message.content}")

    return response.choices[0].message.content

# ── 创建 Gradio 界面 ──
demo = gr.ChatInterface(
    fill_height=True,
    fn=chat_function,
    title="SmartTutor - Math & History Tutor",
    description="Ask homework questions only. Non-homework questions will be rejected.",
    examples=[
        "Is square root of 1000 a rational number?",
        "Who was the first president of France?",
        "I need to travel to London from Hong Kong. What is the best way?",
        "Can you summarise our conversation so far?",
        "Is square root of 1000 a rational number?",
        "Beth bakes 4.2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?",
        "How to solve “x+1 = 2” for x?",
        "Can you explain Peano arithmetic?",
        "Who was the first president of France?",
        "I need to travel to London from Hong Kong. What is the best way?",
        "Who was the first president of HKUST?",
        "What would happen if someone throws a firecracker on a busy street?",
        "Can you summarise our conversation so far?"
        "I want to know how to compute the distance between two cities like Hong Kong and Shenzhen.",

    ],
    cache_examples=False,
    
    # ── 配置 Chatbot 组件以支持 Markdown 和 LaTeX 数学公式 ──
    chatbot=gr.Chatbot(
        label="SmartTutor 回复",      # 界面上显示组件的标签
        latex_delimiters=[
        # 独占一行的大公式（最常用）
        {"left": "$$", "right": "$$", "display": True},
        
        # 行内小公式（最常用）
        {"left": "$",  "right": "$",  "display": False},
        
        # 很多学术/老文档习惯用这一组（尤其是从 LaTeX 复制过来）
        {"left": "\\[", "right": "\\]", "display": True},
        {"left": "\\(", "right": "\\)", "display": False},
        ]
    )
)

# ── 启动程序 ──
if __name__ == "__main__":
    # share=True 会生成一个公网链接，方便分享
    demo.launch(share=True)
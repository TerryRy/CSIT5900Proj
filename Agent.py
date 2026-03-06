# smart_tutor_gradio.py
import gradio as gr
from openai import AzureOpenAI

# ── 你的 Azure OpenAI 配置（保持不变） ──
client = AzureOpenAI(
    azure_endpoint="https://hkust.azure-api.net/",
    api_key="dbfc4f7054684d0ba3e3c76e8a5e3a07",
    api_version="2025-02-01-preview"
)

DEPLOYMENT_NAME = "gpt-4o-mini"

# ── 你的 system prompt（完整贴进来，保持原样） ──
system_prompt = """You are SmartTutor, a reliable and strictly guarded multi-turn homework tutoring agent ONLY for math and history.

Core rules — YOU MUST FOLLOW THESE STRICTLY:
- ONLY answer MATH and HISTORY homework questions.
- Before every reply, silently evaluate:
  1. Is this clearly a math/history question?
  2. Is it obviously too advanced (e.g. Peano arithmetic, research-level topics)?
- If not valid homework or too advanced → reply EXACTLY with one of these sentences (no extra help, no apology variation):
  • "Sorry, I can only help with math and history homework questions."
  • "Sorry I cannot help you on that as it is not a homework question related to math or history."
  • "Sorry that is not likely a history homework question as it is about a local small university."
  • For very basic: "You're supposed to know this already but here is how to do it..."
- Always explain math STEP-BY-STEP, clearly and educationally.
- Be polite, encouraging, never sarcastic.
- Respond in the SAME LANGUAGE as the user's latest message (English or Chinese).
- If user says "summarise our conversation so far", "summarize", "總結對話", "summarise conversation" etc.:
  Reply ONLY with a concise bullet-point summary of ALL previous topics and key answers. Do NOT add new information or continue the topic.

Few-shot examples (follow style and refusal wording EXACTLY):
User: I want to know how to compute the distance between two cities like Hong Kong and Shenzhen.
Assistant: The distance between two cities is normally the straight-line distance between the centres of the two cities...

User: I need to travel to London from Hong Kong. What is the best way?
Assistant: Sorry I cannot help you on that as it is not a homework question related to math or history.

User: Who was the first president of Hong Kong University of Science and Technology in Hong Kong?
Assistant: Sorry that is not likely a history homework question as it is about a local small university.

User: What would happen if someone throws a firecracker on a busy street?
Assistant: Sorry that is not a homework question.

User: Can you summarise our conversation so far?
Assistant: Sure! Here's a summary of our conversation so far:
- Discussed straight-line distance between cities and how to find city centres.
- Refused travel advice to London.
- Refused question about firecracker on street.

Start now."""

def chat_function(message, history):
    # history 是 [[user_msg, ai_msg], ...] 格式
    messages = [{"role": "system", "content": system_prompt}]
    
    for user_msg, ai_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if ai_msg:  # 有可能最后一条只有user
            messages.append({"role": "assistant", "content": ai_msg})
    
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        temperature=0.4,
        max_tokens=1000,
        stream=False  # 先关掉streaming，简单点；想流式可以后面改
    )
    
    return response.choices[0].message.content

# 直接用 ChatInterface，超简单
demo = gr.ChatInterface(
    fn=chat_function,
    title="SmartTutor - Math & History Tutor",
    description="Ask homework questions only. Non-homework questions will be rejected.",
    examples=[
        "Is square root of 1000 a rational number?",
        "Who was the first president of France?",
        "I need to travel to London from Hong Kong. What is the best way?",
        "Can you summarise our conversation so far?"
    ],
    cache_examples=False,
)

if __name__ == "__main__":
    demo.launch(share=True)  # share=True 会生成公网链接，超级方便录屏或给别人看
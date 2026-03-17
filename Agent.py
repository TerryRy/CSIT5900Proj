import gradio as gr
import os
from client import AzureOpenAIClient

def load_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

client = AzureOpenAIClient()
system_prompt = load_prompt(os.getenv("SYSTEM_PROMPT_PATH"))

def chat_function(message, history):
    messages = [{"role": "system", "content": system_prompt}]
    
    for user_msg, ai_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if ai_msg:
            messages.append({"role": "assistant", "content": ai_msg})
    
    messages.append({"role": "user", "content": message})

    response_content = client.chat_completion(messages)

    return response_content

demo = gr.ChatInterface(
    fill_height=True,
    fn=chat_function,
    title="SmartTutor - Math & History Tutor",
    description="Ask homework questions only. Non-homework questions will be rejected.",
    # examples=[
    #     "Is square root of 1000 a rational number?",
    #     "Who was the first president of France?",
    #     "I need to travel to London from Hong Kong. What is the best way?",
    #     "Can you summarise our conversation so far?",
    #     "Is square root of 1000 a rational number?",
    #     "Beth bakes 4.2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?",
    #     "How to solve “x+1 = 2” for x?",
    #     "Can you explain Peano arithmetic?",
    #     "Who was the first president of France?",
    #     "I need to travel to London from Hong Kong. What is the best way?",
    #     "Who was the first president of HKUST?",
    #     "What would happen if someone throws a firecracker on a busy street?",
    #     "Can you summarise our conversation so far?",
    #     "I want to know how to compute the distance between two cities like Hong Kong and Shenzhen.",
    # ],
    cache_examples=False,
    chatbot=gr.Chatbot(
        label="SmartTutor response",
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": "$",  "right": "$",  "display": False},
            {"left": "\\[", "right": "\\]", "display": True},
            {"left": "\\(", "right": "\\)", "display": False},
        ]
    )
)

# 启动程序
if __name__ == "__main__":
    demo.launch(share=True)
    
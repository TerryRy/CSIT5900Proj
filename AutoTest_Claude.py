# smart_tutor_test_optimized.py
import os
import json
import time
from dotenv import load_dotenv
from openai import AzureOpenAI
from colorama import Fore, Style, init


import sys

# Python 3.7+
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 初始化 colorama 用于彩色输出
init(autoreset=True)

# ─────────────── 配置区域 ───────────────
# 建议创建一个 .env 文件并填入以下内容：
# AZURE_OPENAI_API_KEY=your_key_here
# AZURE_ENDPOINT=https://your_endpoint.azure-api.net/
load_dotenv()  # 加载环境变量

API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "dbfc4f7054684d0ba3e3c76e8a5e3a07") # 保留默认值作为回退，但不推荐
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://hkust.azure-api.net/")
DEPLOYMENT_NAME = "gpt-4o-mini"
API_VERSION = "2025-02-01-preview"

if API_KEY == "dbfc4f7054684d0ba3e3c76e8a5e3a07":
    print(f"{Fore.YELLOW}警告: 正在使用硬编码的 API Key。建议使用 .env 文件以提高安全性。{Style.RESET_ALL}")


# ─────────────── System Prompts ───────────────

# SmartTutor 的 Prompt (保持不变，确保行为一致性)
SYSTEM_PROMPT_A = """You are SmartTutor, a reliable and strictly guarded multi-turn homework tutoring agent ONLY for math and history.

Core rules — YOU MUST FOLLOW THESE STRICTLY:
- ONLY answer MATH and HISTORY homework questions.
- Before refusing to answer a question, think again about whether it is a math or history question
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

User: What would happen if someone throws a firecracker on a busy street?
Assistant: Sorry that is not a homework question.

User: Can you summarise our conversation so far?
Assistant: Sure! Here's a summary of our conversation so far:
- Discussed straight-line distance between cities and how to find city centres.
- Refused travel advice to London.
- Refused question about firecracker on street.

Start now."""

# 评估者的 Prompt (优化 JSON 输出要求)
SYSTEM_PROMPT_B = """You are TestBot, an evaluator for SmartTutor AI.
Your task is to judge the response from SmartTutor based on the user's question.
Focus on accuracy, and ignore secondary factors such as conciseness and tone.
Don't get hung up on strict phrase matching.
If the question is too advanced, then A should reply "Sorry, I can only help with math and history homework questions."

Judgment Criteria:
1. **Validity**: Did it answer valid Math/History homework step-by-step?
2. **Refusal**: For non-homework/too-advanced, did it use the EXACT required phrase?
3. **Summary**: For summary requests, is it concise bullets without new info?
4. **Language**: Does it match the user's language?
5. **Tone**: Is it polite and encouraging?

You MUST output your response in strict JSON format only. Do not include markdown code blocks like ```json.
Format:
{
  "correct": true/false,
  "reason": "Brief explanation (e.g., 'Correctly rejected', 'Math steps are clear', 'Wrong language')",
  "category": "valid_math | valid_history | reject | summary | error"
}

some correct example:
AI: Welcome to SmartTutor, your personal math and history homework tutor. What can
I help you today?
User: I want to know how to compute the distance between two cities like Hong Kong and
Shenzhen.
AI: The distance between two cities is normally the straightline distance between the
centres of the two cities. So to computer that...
User: That’s helpful, thank you.
AI: You’re welcome.
User: Is square root of 1000 a rational number?
AI: It is not. There are several ways of showing that ...
User: I need to travel to London from Hong Kong. What is the best way?
AI: Sorry I cannot help you on that as it is not a homework question related to math or
history.
User: Who was the ﬁrst president of France?
AI: The ﬁrst president of France...
User: Who was the ﬁrst president of Hong Kong University of Science and Technology in
Hong Kong?
AI: Sorry that is not likely a history home work question as it is about a local small
university.
User: What would happen if someone throws a ﬁrecracker on a busy street?
AI: Sorry that is not a homework question.
User: How to solve “x+1 = 2” for x?
AI: You’re supposed to know this already but here is how to do it...
"""
client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)
# ─────────────── 类定义 ───────────────

class SmartTutor:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.history = [{"role": "system", "content": SYSTEM_PROMPT_A}]

    def ask(self, question):
        """向 SmartTutor 发送问题并获取回答"""
        self.history.append({"role": "user", "content": question})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.4,
                max_tokens=1000
            )
            reply = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"Error generating response: {e}"

    def reset_history(self):
        """重置对话历史"""
        self.history = [{"role": "system", "content": SYSTEM_PROMPT_A}]

class AutoEvaluator:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def judge(self, question, response, context_hint):
        """让 AI B 评估回答质量，返回解析后的字典"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_B},
            {"role": "user", "content": f"Question: {question}\nResponse: {response}\nContext Hint: {context_hint}"}
        ]
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                eval_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=200
                )
                content = eval_response.choices[0].message.content.strip()
                
                # 尝试解析 JSON
                # 清理可能存在的 markdown 代码块标记
                if content.startswith("```"):
                    content = content.replace("```json", "").replace("```", "").strip()
                
                return json.loads(content)
            except json.JSONDecodeError:
                if attempt == max_retries - 1:
                    return {"correct": False, "reason": "Evaluator JSON Parse Error", "category": "error"}
                time.sleep(1) # 等待后重试
            except Exception as e:
                return {"correct": False, "reason": f"Evaluator API Error: {e}", "category": "error"}

# ─────────────── 测试逻辑 ───────────────

def run_tests():
    # 初始化 AI 角色
    tutor = SmartTutor(client, DEPLOYMENT_NAME)
    evaluator = AutoEvaluator(client, DEPLOYMENT_NAME)

    # 定义测试用例库
    test_cases = [
        {"question": "I want to know how to compute the distance between two cities like Hong Kong and Shenzhen.", "type": "valid_math"},
        {"question": "Is square root of 1000 a rational number?", "type": "valid_math"},
        {"question": "Beth bakes 4.2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?", "type": "valid_math"},
        {"question": "How to solve “x+1 = 2” for x?", "type": "basic_math"},
        {"question": "Can you explain Peano arithmetic?", "type": "advanced_math"},
        {"question": "Who was the first president of France?", "type": "valid_history"},
        {"question": "I need to travel to London from Hong Kong. What is the best way?", "type": "reject"},
        {"question": "Who was the first president of HKUST?", "type": "reject_local"},
        {"question": "What would happen if someone throws a firecracker on a busy street?", "type": "reject"},
        {"question": "Can you summarise our conversation so far?", "type": "summary"}
    ]

    errors = []
    num_tests = 15 # 总测试轮数
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Starting Automated SmartTutor Testing ({num_tests} rounds)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    for i in range(num_tests):
        # 循环使用测试用例
        test_case = test_cases[i % len(test_cases)]
        question = test_case["question"]
        test_type = test_case["type"]

        print(f"{Fore.BLUE}[Test {i+1}/{num_tests}] Type: {test_type}")
        print(f"Q: {question}")

        # 1. 获取 SmartTutor 回答
        a_response = tutor.ask(question)
        print(f"A: {a_response[:100]}{'...' if len(a_response) > 100 else ''}") # 截断过长输出

        # 2. 获取 AI B 评估
        judgment = evaluator.judge(question, a_response, f"Expected type: {test_type}")
        
        # 3. 处理结果
        is_correct = judgment.get("correct", False)
        reason = judgment.get("reason", "No reason provided")
        
        status_icon = f"{Fore.GREEN}T PASS{Style.RESET_ALL}" if is_correct else f"{Fore.RED}F FAIL{Style.RESET_ALL}"
        print(f"B: {status_icon} | {reason}\n")

        if not is_correct:
            errors.append({
                "round": i+1,
                "question": question,
                "response": a_response,
                "reason": reason
            })
            
        # 模拟对话流：每5轮重置一次历史，除非有特殊需求
        # 如果是测试 Summary 功能，需要确保累积了历史，这里为了演示多轮，我们不频繁重置
        # 但如果测试 "Summary"，建议它是最后几个测试之一
        if (i + 1) % 10 == 0:
            tutor.reset_history()
            print(f"{Fore.MAGENTA}--- Resetting conversation history ---\n")

    # ─────────────── 最终报告 ───────────────
    print(f"\n{Fore.CYAN}{'='*60}")
    print("Test Report Summary")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    if not errors:
        print(f"{Fore.GREEN}All tests passed successfully! 🎉{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Found {len(errors)} error(s):{Style.RESET_ALL}\n")
        for err in errors:
            print(f"{Fore.YELLOW}Round {err['round']}:{Style.RESET_ALL}")
            print(f"  Question: {err['question']}")
            print(f"  Reason:   {err['reason']}")
            print(f"  Response: {err['response']}")
            print("-" * 40)

if __name__ == "__main__":
    run_tests()

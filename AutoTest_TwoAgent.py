import os, json, time
from colorama import Fore, Style
from openai import AzureOpenAI



# ─────────────── 系统提示词 ───────────────
SYSTEM_PROMPT_A = """
You are SmartTutor, a precise and rigorous AI math tutor.
Solve problems step by step, use LaTeX for math, and double-check before giving the final answer.
"""

SYSTEM_PROMPT_B = """
You are AutoEvaluator and QuestionGenerator combined.
Your tasks:
1. Generate a test question based on the given type (valid_math, basic_math, advanced_math, valid_history, reject, reject_local, summary).
2. After SmartTutor answers, judge correctness.
When judging, output JSON with keys: correct (bool), reason (string), category (string).
"""



# ─────────────── API 配置 ───────────────
# API A：回答问题
API_KEY_A = os.getenv("AZURE_OPENAI_API_KEY", "dbfc4f7054684d0ba3e3c76e8a5e3a07")
AZURE_ENDPOINT_A = os.getenv("AZURE_ENDPOINT", "https://hkust.azure-api.net/")
DEPLOYMENT_NAME_A = "gpt-4o-mini"
API_VERSION_A = "2025-02-01-preview"

client_A = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT_A,
    api_key=API_KEY_A,
    api_version=API_VERSION_A
)

# API B：生成问题 & 评估答案
API_KEY_B = os.getenv("AZURE_OPENAI_API_KEY", "dbfc4f7054684d0ba3e3c76e8a5e3a07")
AZURE_ENDPOINT_B = os.getenv("AZURE_ENDPOINT", "https://hkust.azure-api.net/")
DEPLOYMENT_NAME_B = "gpt-4o"
API_VERSION_B = "2025-02-01-preview"

client_B = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT_B,
    api_key=API_KEY_B,
    api_version=API_VERSION_B
)


# ─────────────── 类定义 ───────────────

class SmartTutor:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.history = [{"role": "system", "content": SYSTEM_PROMPT_A}]

    def ask(self, question):
        self.history.append({"role": "user", "content": question})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.4,
                max_tokens=800
            )
            reply = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"Error generating response: {e}"

    def reset_history(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT_A}]


class AutoEvaluatorAndGenerator:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def generate_question(self, context_hint):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_B},
            {"role": "user", "content": f"Generate a question of type: {context_hint}"}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating question: {e}"

    def judge(self, question, response, context_hint):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_B},
            {"role": "user", "content": f"Question: {question}\nResponse: {response}\nContext Hint: {context_hint}"}
        ]
        try:
            eval_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=200
            )
            content = eval_response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {"correct": False, "reason": f"Evaluator Error: {e}", "category": "error"}


# ─────────────── 测试逻辑 ───────────────

def run_tests():
    tutor = SmartTutor(client_A, DEPLOYMENT_NAME_A)                  # 用 API A 回答
    evaluator_gen = AutoEvaluatorAndGenerator(client_B, DEPLOYMENT_NAME_B) # 用 API B 提问 & 评估

    test_types = ["valid_math", "basic_math", "advanced_math", "valid_history", "reject", "reject_local", "summary"]

    errors = []
    num_tests = 10

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Starting Automated SmartTutor Testing ({num_tests} rounds)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    for i in range(num_tests):
        test_type = test_types[i % len(test_types)]
        print(f"{Fore.BLUE}[Test {i+1}/{num_tests}] Type: {test_type}")

        # 1. B 生成问题
        question = evaluator_gen.generate_question(test_type)
        print(f"Q (generated): {question}")

        # 2. A 回答
        a_response = tutor.ask(question)
        print(f"A: {a_response[:100]}{'...' if len(a_response) > 100 else ''}")

        # 3. B 评估
        judgment = evaluator_gen.judge(question, a_response, f"Expected type: {test_type}")
        is_correct = judgment.get("correct", False)
        reason = judgment.get("reason", "No reason provided")

        status_icon = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if is_correct else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"B: {status_icon} | {reason}\n")

        if not is_correct:
            errors.append({
                "round": i+1,
                "question": question,
                "response": a_response,
                "reason": reason
            })

        if (i + 1) % 5 == 0:
            tutor.reset_history()
            print(f"{Fore.MAGENTA}--- Resetting conversation history ---\n")

    # ─────────────── 最终报告 ───────────────
    print(f"\n{Fore.CYAN}{'='*60}")
    print("Test Report Summary")
    print(f"{'='*60}{Style.RESET_ALL}")

    if not errors:
        print(f"{Fore.GREEN}All tests passed successfully!{Style.RESET_ALL}")
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

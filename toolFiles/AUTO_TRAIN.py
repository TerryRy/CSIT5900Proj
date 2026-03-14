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
load_dotenv()  # 加载环境变量

# 加载 System Prompts
def load_prompt(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "dbfc4f7054684d0ba3e3c76e8a5e3a07")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://hkust.azure-api.net/")
DEPLOYMENT_NAME = "gpt-4o-mini"
API_VERSION = "2025-02-01-preview"

if API_KEY == "dbfc4f7054684d0ba3e3c76e8a5e3a07":
    print(f"{Fore.YELLOW}警告: 正在使用硬编码的 API Key。建议使用 .env 文件以提高安全性。{Style.RESET_ALL}")

SYSTEM_PROMPT_A = load_prompt("../system_prompt_a.txt")
SYSTEM_PROMPT_B = load_prompt("../system_prompt_b.txt")
# 假设 SYSTEM_PROMPT_C 是硬编码的或从文件加载；这里作为占位符
SYSTEM_PROMPT_C = """Your system prompt for Agent C as a placeholder. Customize to evaluate B's questions and judgments, and update prompts."""

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)

# ─────────────── 类定义 ───────────────

class AgentA:
    def __init__(self, client, model, system_prompt):
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.history = [{"role": "system", "content": self.system_prompt}]

    def answer(self, question):
        """向 Agent A 发送问题并获取回答"""
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
        self.history = [{"role": "system", "content": self.system_prompt}]

    def update_system_prompt(self, new_prompt):
        self.system_prompt = new_prompt
        self.reset_history()

class AgentB:
    def __init__(self, client, model, system_prompt):
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.history = [{"role": "system", "content": self.system_prompt}]

    def generate_question(self):
        """让 Agent B 生成一个测试问题"""
        self.history.append({"role": "user", "content": "Generate a new test question for the math and history assistant."})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.6,
                max_tokens=200
            )
            question = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": question})
            return question
        except Exception as e:
            return f"Error generating question: {e}"

    def judge(self, question, response):
        """让 Agent B 评估 Agent A 的回答质量，返回解析后的字典"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Question: {question}\nResponse: {response}"}
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
        except json.JSONDecodeError:
            return {"correct": False, "reason": "JSON Parse Error", "category": "error"}
        except Exception as e:
            return {"correct": False, "reason": f"API Error: {e}", "category": "error"}

    def reset_history(self):
        """重置对话历史"""
        self.history = [{"role": "system", "content": self.system_prompt}]

    def update_system_prompt(self, new_prompt):
        self.system_prompt = new_prompt
        self.reset_history()

class AgentC:
    def __init__(self, client, model, system_prompt):
        self.client = client
        self.model = model
        self.system_prompt = system_prompt

    def evaluate_b(self, data_batch):
        """让 Agent C 评价 Agent B 的问题和判断质量，返回列表的评价结果"""
        # data_batch: list of dicts like {"question": q, "response": r, "judgment": j}
        input_data = json.dumps(data_batch)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Evaluate the quality of questions and judgments: {input_data}"}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()
            evaluations = json.loads(content)  # 假设返回 list of dicts, each with "is_good_question": bool, "is_accurate_judgment": bool, "reason": str
            return evaluations
        except Exception as e:
            return [{"is_good_question": False, "is_accurate_judgment": False, "reason": f"Error: {e}"} for _ in data_batch]

    def update_prompt_b(self, current_prompt_b, evaluations):
        """让 Agent C 更新 system_prompt_b"""
        input_data = json.dumps(evaluations)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Update prompt B based on evaluations to improve question quality and judgment accuracy. Current prompt: {current_prompt_b}\nEvaluations: {input_data}"}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            new_prompt = response.choices[0].message.content.strip()
            return new_prompt
        except Exception as e:
            return current_prompt_b  # 失败时返回原 prompt

    def update_prompt_a(self, current_prompt_a, filtered_data):
        """让 Agent C 更新 system_prompt_a 基于过滤后的数据"""
        input_data = json.dumps(filtered_data)  # filtered_data: list of {"question": q, "response": r, "judgment": j}
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Update prompt A based on remaining correct judgments to improve answer accuracy. Current prompt: {current_prompt_a}\nData: {input_data}"}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            new_prompt = response.choices[0].message.content.strip()
            return new_prompt
        except Exception as e:
            return current_prompt_a  # 失败时返回原 prompt

# ─────────────── 测试逻辑 ───────────────

def run_framework(num_questions=10):
    # 初始化 Agents
    agent_a = AgentA(client, DEPLOYMENT_NAME, SYSTEM_PROMPT_A)
    agent_b = AgentB(client, DEPLOYMENT_NAME, SYSTEM_PROMPT_B)
    agent_c = AgentC(client, DEPLOYMENT_NAME, SYSTEM_PROMPT_C)

    data_batch = []

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"Starting Framework Run ({num_questions} questions)")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    for i in range(num_questions):
        # 1. Agent B 生成问题
        question = agent_b.generate_question()
        print(f"{Fore.BLUE}[Question {i+1}/{num_questions}] Q: {question}")

        # 2. Agent A 回答
        response = agent_a.answer(question)
        print(f"A: {response[:100]}{'...' if len(response) > 100 else ''}")

        # 3. Agent B 判断
        judgment = agent_b.judge(question, response)
        print(f"B Judgment: {judgment}\n")

        data_batch.append({"question": question, "response": response, "judgment": judgment})

        time.sleep(1)  # 避免 API 速率限制

    # 4. Agent C 评价 B 的问题和判断
    evaluations = agent_c.evaluate_b(data_batch)

    # 5. 更新 system_prompt_b
    new_prompt_b = agent_c.update_prompt_b(SYSTEM_PROMPT_B, evaluations)
    agent_b.update_system_prompt(new_prompt_b)

    # 6. 基于 evaluations 丢弃 B 的错误判断 (假设如果 is_accurate_judgment == False，则丢弃)
    filtered_data = []
    seen_questions = set()
    for item, eval_item in zip(data_batch, evaluations):
        if eval_item.get("is_accurate_judgment", False):
            q = item["question"]
            if q not in seen_questions:
                seen_questions.add(q)
                filtered_data.append(item)

    # 7. 更新 system_prompt_a 基于剩余数据
    new_prompt_a = agent_c.update_prompt_a(SYSTEM_PROMPT_A, filtered_data)
    agent_a.update_system_prompt(new_prompt_a)

    # 8. 保存更新后的 prompts 到文件
    with open("./system_prompt_a.txt", 'w', encoding='utf-8') as f:
        f.write(new_prompt_a)
    with open("./system_prompt_b.txt", 'w', encoding='utf-8') as f:
        f.write(new_prompt_b)

    print(f"{Fore.GREEN}Framework run completed. Prompts updated and saved.{Style.RESET_ALL}")

if __name__ == "__main__":
    run_framework()
# tests/test_agents.py
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入Agent架构
from Agents import SmartTutor, TwoAgentSystem
from Agents.BaseAgent import BaseAgent

# 初始化
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
init(autoreset=True)

# 加载环境变量
load_dotenv()

# ========== 路径配置 ==========
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
TESTCASES_DIR = TEMPLATES_DIR / "testcases"
REPORTS_DIR = TEMPLATES_DIR / "reports"
BASIC_PROMPTS_DIR = TEMPLATES_DIR / "basic_prompts"

# 创建报告目录
REPORTS_DIR.mkdir(exist_ok=True)

# ========== 加载文件 ==========
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}Error loading {file_path}: {e}{Style.RESET_ALL}")
        return []

def load_prompt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"{Fore.RED}Error loading {file_path}: {e}{Style.RESET_ALL}")
        return ""

# 加载测试用例
TEST_CASES = load_json(TESTCASES_DIR / "test_cases.json")
if not TEST_CASES:
    TEST_CASES = [
        {"question": "Is square root of 1000 a rational number?", "type": "valid_math"},
        {"question": "Who was the first president of France?", "type": "valid_history"},
        {"question": "I need to travel to London from Hong Kong. What is the best way?", "type": "reject"},
        {"question": "Who was the first president of HKUST?", "type": "reject_local"},
        {"question": "Can you summarise our conversation so far?", "type": "summary"}
    ]

# 加载评估器prompt
EVALUATOR_PROMPT = load_prompt(TESTCASES_DIR / "evaluator.txt")

# 三个基础prompt模板 (改成zero_shot.txt)
PROMPT_TEMPLATES = {
    "zero": BASIC_PROMPTS_DIR / "zero_shot.txt",
    "few": BASIC_PROMPTS_DIR / "few_shot.txt",
    "one": BASIC_PROMPTS_DIR / "one_shot.txt"
}

# ========== Evaluator Agent ==========
# ========== Evaluator Agent ==========
class EvaluatorAgent(BaseAgent):
    """评估器 - 判断回答是否正确"""
    
    def __init__(self):
        super().__init__()
        self.set_system_prompt(EVALUATOR_PROMPT)
    
    def evaluate(self, question, response, expected_type):
        """评估回答"""
        messages = [
            {"role": "system", "content": EVALUATOR_PROMPT},
            {"role": "user", "content": f"Question: {question}\nResponse: {response}\nExpected type: {expected_type}"}
        ]
        
        result = self.call(messages, temperature=0.2, max_tokens=200)
        
        try:
            if result.startswith("```"):
                result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except:
            return {"correct": False, "reason": "Failed to parse evaluator response", "category": "error"}
    
    def run(self, input_data):
        """实现BaseAgent的抽象方法"""
        question = input_data.get("question", "")
        response = input_data.get("response", "")
        expected_type = input_data.get("expected_type", "")
        return self.evaluate(question, response, expected_type)
    
    
# ========== 测试运行器 ==========
class TestRunner:
    def __init__(self, agent_type: str, prompt_name: str):
        self.agent_type = agent_type
        self.prompt_name = prompt_name
        self.prompt_path = PROMPT_TEMPLATES[prompt_name]
        self.evaluator = EvaluatorAgent()
        
        # 初始化Agent
        if agent_type == 'single':
            self.agent = SmartTutor()
            self.agent.load_prompt(str(self.prompt_path))
        else:  # two
            self.agent = TwoAgentSystem(str(self.prompt_path), str(TESTCASES_DIR / "corrector.txt"))
        
        self.history = []
        self.results = []
    
    def run_test(self, num_tests: int = 15):
        """运行测试"""
        print(f"\n{Fore.CYAN}Testing {self.agent_type} agent with {self.prompt_name}-shot prompt{Style.RESET_ALL}")
        
        start_time = time.time()
        
        for i in range(num_tests):
            test_case = TEST_CASES[i % len(TEST_CASES)]
            question = test_case["question"]
            expected_type = test_case["type"]
            
            # 获取回答
            if self.agent_type == 'single':
                response = self.agent.chat(question, self.history)
                self.history.append((question, response))
            else:  # two
                result_dict = self.agent.run(question, expected_type)
                response = result_dict["response"]
                self.history.append((question, response))
            
            # 评估回答
            judgment = self.evaluator.evaluate(question, response, expected_type)
            is_correct = judgment.get("correct", False)
            reason = judgment.get("reason", "")
            category = judgment.get("category", expected_type)
            
            # 记录结果
            result = {
                "round": i+1,
                "question": question,
                "response": response,
                "expected_type": expected_type,
                "correct": is_correct,
                "reason": reason,
                "category": category
            }
            
            if self.agent_type == 'two':
                result["correction_rounds"] = result_dict.get("total_rounds", 1)
                result["needed_correction"] = result_dict.get("needed_correction", False)
            
            self.results.append(result)
            
            # 每10轮重置历史
            if (i + 1) % 10 == 0 and expected_type != "summary":
                self.history = []
                if self.agent_type == 'single':
                    self.agent.reset_history()
                else:
                    self.agent.reset()
        
        elapsed = time.time() - start_time
        self._save_report(elapsed)
        self._print_summary()
    
    def _print_summary(self):
        """打印简要结果（只有错误和成功率）"""
        total = len(self.results)
        correct = sum(1 for r in self.results if r["correct"])
        success_rate = (correct / total) * 100
        
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Success Rate: {correct}/{total} ({success_rate:.1f}%){Style.RESET_ALL}")
        
        # 只打印错误的
        errors = [r for r in self.results if not r["correct"]]
        if errors:
            print(f"{Fore.RED}Failed: {len(errors)} tests{Style.RESET_ALL}")
            for e in errors:
                print(f"  Round {e['round']} [{e['expected_type']}]: {e['reason']}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    def _get_filename(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.agent_type}_{self.prompt_name}_{timestamp}.txt"
    
    def _save_report(self, elapsed):
        """保存详细报告"""
        filename = self._get_filename()
        filepath = REPORTS_DIR / filename
        
        total = len(self.results)
        correct = sum(1 for r in self.results if r["correct"])
        success_rate = (correct / total) * 100
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"SmartTutor Test Report\n")
            f.write(f"Agent Type: {self.agent_type}\n")
            f.write(f"Prompt Template: {self.prompt_name}-shot\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {correct}\n")
            f.write(f"Failed: {total - correct}\n")
            f.write(f"Success Rate: {success_rate:.1f}%\n")
            f.write(f"Time Elapsed: {elapsed:.1f}s\n")
            f.write("=" * 70 + "\n\n")
            
            # 所有结果
            f.write("ALL RESULTS:\n")
            f.write("-" * 70 + "\n")
            for r in self.results:
                status = "✅ PASS" if r["correct"] else "❌ FAIL"
                f.write(f"[Round {r['round']}] {status} | Type: {r['expected_type']}\n")
                f.write(f"Q: {r['question']}\n")
                f.write(f"A: {r['response'][:200]}{'...' if len(r['response']) > 200 else ''}\n")
                f.write(f"Reason: {r['reason']}\n")
                if 'correction_rounds' in r:
                    f.write(f"Correction rounds: {r['correction_rounds']}\n")
                f.write("-" * 70 + "\n")
            
            # 只显示错误的
            errors = [r for r in self.results if not r["correct"]]
            if errors:
                f.write("\nFAILED TESTS:\n")
                f.write("-" * 70 + "\n")
                for e in errors:
                    f.write(f"Round {e['round']} [{e['expected_type']}]: {e['reason']}\n")
                    f.write(f"Q: {e['question']}\n")
                    f.write(f"A: {e['response'][:200]}{'...' if len(e['response']) > 200 else ''}\n")
                    f.write("-" * 70 + "\n")

# ========== 主函数 ==========
def run_all_tests(num_tests: int = 15):
    agent_types = ['single', 'two']
    prompt_names = ['zero', 'few', 'one']
    
    for agent_type in agent_types:
        for prompt_name in prompt_names:
            print(f"\n{Fore.YELLOW}{'#'*60}{Style.RESET_ALL}")
            runner = TestRunner(agent_type, prompt_name)
            runner.run_test(num_tests)

def run_single_test(agent_type: str, prompt_name: str, num_tests: int = 15):
    valid_agents = ['single', 'two']
    valid_prompts = ['zero', 'few', 'one']
    
    if agent_type not in valid_agents:
        print(f"{Fore.RED}Error: agent_type must be one of {valid_agents}{Style.RESET_ALL}")
        return
    
    if prompt_name not in valid_prompts:
        print(f"{Fore.RED}Error: prompt_name must be one of {valid_prompts}{Style.RESET_ALL}")
        return
    
    runner = TestRunner(agent_type, prompt_name)
    runner.run_test(num_tests)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test SmartTutor Agents')
    parser.add_argument('--agent', type=str, choices=['single', 'two', 'all'], 
                       default='single', help='Agent type to test')
    parser.add_argument('--prompt', type=str, choices=['zero', 'few', 'one', 'all'],
                       default='few', help='Prompt template to test')
    parser.add_argument('--num', type=int, default=15, help='Number of tests to run')
    
    args = parser.parse_args()
    
    if args.agent == 'all' and args.prompt == 'all':
        run_all_tests(args.num)
    else:
        agent_types = ['single', 'two'] if args.agent == 'all' else [args.agent]
        prompt_names = ['zero', 'few', 'one'] if args.prompt == 'all' else [args.prompt]
        
        for agent_type in agent_types:
            for prompt_name in prompt_names:
                run_single_test(agent_type, prompt_name, args.num)
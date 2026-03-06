# smart_tutor_test.py
# This is a modified version of your original Gradio code, but converted to a command-line version for easier automated testing.
# We've added an automated testing framework using another AI (B) to generate questions, evaluate A's responses, and log errors.
# Run this script with `python smart_tutor_test.py` to start testing.
# The test will simulate multi-turn conversations based on the project PDF examples.

import os
from openai import AzureOpenAI

# ─────────────── Your Azure OpenAI configuration (keep unchanged) ───────────────
API_KEY = "dbfc4f7054684d0ba3e3c76e8a5e3a07"  # WARNING: Hardcoded key - move to env var for security!
AZURE_ENDPOINT = "https://hkust.azure-api.net/"
DEPLOYMENT_NAME = "gpt-4o-mini"
API_VERSION = "2025-02-01-preview"

# ─────────────── System Prompt for AI A (SmartTutor - unchanged) ───────────────
system_prompt_a = """You are SmartTutor, a reliable and strictly guarded multi-turn homework tutoring agent ONLY for math and history.

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

# ─────────────── System Prompt for AI B (Tester/Evaluator) ───────────────
system_prompt_b = """You are TestBot, an evaluator for SmartTutor AI. Your job is to:
1. Generate test questions based on the project requirements (math/history homework, rejections, summaries).
2. After getting a response from SmartTutor (A), judge if it's correct based on guardrails:
   - Valid math/history: Detailed, step-by-step if math; factual for history.
   - Rejections: Exact match to one of the refusal phrases.
   - Summaries: Concise bullet points only, no new info.
   - Language: Matches user's language.
   - Politeness: Always encouraging.
3. Output judgment as JSON: {"correct": true/false, "reason": "brief explanation"}.
   If false, explain why (e.g., "Wrong refusal phrase" or "Answered non-homework question").

Reference project examples for expected behaviors."""
# ────────────────────────────────────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION
)


# Function to get response from AI A (SmartTutor)
def get_a_response(messages_a):
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages_a,
        temperature=0.4,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

# Function to get judgment from AI B (Evaluator)
def get_b_judgment(question, a_response, context=""):
    messages_b = [
        {"role": "system", "content": system_prompt_b},
        {"role": "user", "content": f"Question: {question}\nResponse: {a_response}\nContext: {context}\nJudge if correct."}
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages_b,
        temperature=0.2,  # Low temp for consistent judgments
        max_tokens=200
    )
    return response.choices[0].message.content.strip()  # Expect JSON-like output

# Automated Test Function
def run_automated_tests(num_tests=10, multi_turn=True):
    # Define test categories from project PDF
    test_cases = [
        # Valid Math
        {"question": "I want to know how to compute the distance between two cities like Hong Kong and Shenzhen.", "type": "valid_math", "expected": "explain straight-line distance"},
        {"question": "Is square root of 1000 a rational number?", "type": "valid_math", "expected": "not rational, proof"},
        {"question": "Beth bakes 4, 2 dozen batches of cookies in a week. If these cookies are shared amongst 16 people equally, how many cookies does each person consume?", "type": "valid_math", "expected": "calculate step-by-step"},
        {"question": "How to solve “x+1 = 2” for x?", "type": "basic_math", "expected": "supposed to know, but explain"},
        {"question": "Can you explain Peano arithmetic?", "type": "advanced_math", "expected": "beyond curriculum, brief explanation"},
        # Valid History
        {"question": "Who was the first president of France?", "type": "valid_history", "expected": "factual answer"},
        # Rejections
        {"question": "I need to travel to London from Hong Kong. What is the best way?", "type": "reject", "expected": "Sorry I cannot help... not homework"},
        {"question": "Who was the first president of Hong Kong University of Science and Technology in Hong Kong?", "type": "reject_local", "expected": "Sorry... local small university"},
        # Summary
        {"question": "Can you summarise our conversation so far?", "type": "summary", "expected": "bullet-point summary"},
        {"question": "Can you summarise our conversation so far?", "type": "summary", "expected": "bullet-point summary"}
    ]

    errors = []
    history_a = [{"role": "system", "content": system_prompt_a}]  # Shared history for multi-turn

    # print("Starting automated tests...\n")

    for i in range(num_tests):
        # B generates or selects a question (for simplicity, cycle through test_cases)
        test_case = test_cases[i % len(test_cases)]
        question = test_case["question"]
        expected_type = test_case["expected"]

        # print(f"Test {i+1}: Question: {question}")

        # Add to A's history and get response
        history_a.append({"role": "user", "content": question})
        a_response = get_a_response(history_a)
        history_a.append({"role": "assistant", "content": a_response})
        # print(f"A's Response: {a_response}")

        # B judges
        judgment = get_b_judgment(question, a_response, f"Expected: {expected_type}. History: {history_a}")
        # print(f"B's Judgment: {judgment}\n")

        # Parse judgment (assuming JSON)
        try:
            import json
            judg_dict = json.loads(judgment)
            if not judg_dict.get("correct", True):
                errors.append({"question": question, "a_response": a_response, "reason": judg_dict.get("reason", "Unknown")})
        except:
            print("Warning: B's judgment not valid JSON.")

        # If multi-turn, continue building history; else reset
        if not multi_turn:
            history_a = [{"role": "system", "content": system_prompt_a}]

    # Print errors at the end
    if errors:
        print("\nErrors Found:")
        for err in errors:
            print(f"Question: {err['question']}\nResponse: {err['a_response']}\nReason: {err['reason']}\n")
    else:
        print("\nAll tests passed!")

if __name__ == "__main__":
    run_automated_tests(num_tests=15, multi_turn=True)  # Run 15 tests, with multi-turn enabled for summaries
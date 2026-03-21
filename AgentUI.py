import gradio as gr
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Agent architectures
from Agents import SmartTutor, TwoAgentSystem
from Agents.EmbAgent import EmbAgent

# ========== command lines ==========
parser = argparse.ArgumentParser(description='SmartTutor UI - Math & History Tutor')
parser.add_argument('--agent', type=str, default='emb', choices=['single', 'two', 'emb'],
                    help='Agent architecture: single, two, or emb')
parser.add_argument('--manager', action='store_true', help='Enable conversation manager')
parser.add_argument('--examples', action='store_true', help='Enable examples')
args = parser.parse_args()

# Configuration
AGENT_TYPE = args.agent
ENABLE_CONVERSATION_MANAGER = args.manager
USE_EXAMPLES = args.examples

# ========== Path Configuration ==========
PROMPT_PATH = os.getenv("SYSTEM_PROMPT_PATH", "./templates/basic_prompts/few_shot.txt")
CORRECTOR_PATH = os.getenv("CORRECTOR_PROMPT_PATH", "./templates/testcases/corrector.txt")
EXAMPLE_FILE_PATH = os.getenv("EXAMPLES_FILE_PATH") if USE_EXAMPLES else None
print("-----------Using Prompt Template:------------", PROMPT_PATH)
print("-----------Using Corrector Template:------------", CORRECTOR_PATH)

# ========== Conversation Manager ==========
if ENABLE_CONVERSATION_MANAGER:
    try:
        from toolFiles.conversation_manager import ConversationManager
        conversation_mgr = ConversationManager()
    except ImportError:
        ENABLE_CONVERSATION_MANAGER = False

# ========== Initialize Agent ==========
if AGENT_TYPE == 'single':
    agent = SmartTutor()
    agent.load_prompt(PROMPT_PATH)
elif AGENT_TYPE == 'two':
    agent = TwoAgentSystem(PROMPT_PATH, CORRECTOR_PATH)
else:  # emb
    agent = EmbAgent()
    agent.load_prompt(PROMPT_PATH)

# ========== Load Examples ==========
def load_examples_from_file():
    if not USE_EXAMPLES or not EXAMPLE_FILE_PATH:
        return None
    try:
        with open(EXAMPLE_FILE_PATH, "r", encoding="utf-8") as f:
            examples = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return examples
    except FileNotFoundError:
        return None

examples = load_examples_from_file()

# ========== Chat Function ==========
def chat_function(message, history):
    if ENABLE_CONVERSATION_MANAGER:
        history = conversation_mgr.compress_history(history)
    
    if AGENT_TYPE == 'single':
        response = agent.chat(message, history)
    elif AGENT_TYPE == 'two':
        # Two agent system returns dict with response
        result = agent.run(message)
        response = result.get("response", "")
    else:  # emb
        response = agent.chat(message, history)
    
    if ENABLE_CONVERSATION_MANAGER:
        conversation_mgr.update_topic(message, response)
    
    return response

# ========== Gradio Interface ==========
demo = gr.ChatInterface(
    fill_height=True,
    fn=chat_function,
    title="SmartTutor - Math & History Tutor",
    description="Ask homework questions only. Non-homework questions will be rejected.",
    examples=examples,
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

if __name__ == "__main__":
    demo.launch(share=True)
# run_command_line.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import Agent architectures
from Agents import SmartTutor, TwoAgentSystem

# Load environment variables
load_dotenv()

# ========== Path Configuration ==========
PROMPT_PATH = os.getenv("SYSTEM_PROMPT_PATH", "./templates/basic_prompts/zero_shot.txt")
CORRECTOR_PATH = os.getenv("CORRECTOR_PROMPT_PATH", "./templates/testcases/corrector.txt")

def run_single():
    """Run single agent in command line"""
    agent = SmartTutor()
    agent.load_prompt(PROMPT_PATH)
    
    print("\n" + "="*50)
    print("SmartTutor - Single Agent (Command Line)")
    print("="*50)
    print("Type 'exit' to quit, 'reset' to clear history\n")
    
    history = []
    
    while True:
        try:
            question = input("\nYou: ").strip()
            
            if question.lower() == 'exit':
                print("Goodbye!")
                break
            elif question.lower() == 'reset':
                history = []
                agent.reset_history()
                print("History cleared")
                continue
            elif not question:
                continue
            
            # Get response
            response = agent.chat(question, history)
            history.append((question, response))
            
            print(f"\nSmartTutor: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def run_two():
    """Run two-agent system in command line"""
    agent = TwoAgentSystem(PROMPT_PATH, CORRECTOR_PATH)
    
    print("\n" + "="*50)
    print("SmartTutor - Two-Agent System (with auto-correction)")
    print("="*50)
    print("Type 'exit' to quit, 'reset' to clear history, 'stats' to see correction stats\n")
    
    while True:
        try:
            question = input("\nYou: ").strip()
            
            if question.lower() == 'exit':
                print("Goodbye!")
                break
            elif question.lower() == 'reset':
                agent.reset()
                print("History cleared")
                continue
            elif question.lower() == 'stats':
                stats = agent.get_correction_stats()
                print(f"\nCorrection Stats:")
                print(f"  Total questions: {stats.get('total', 0)}")
                print(f"  Needed correction: {stats.get('corrected', 0)}")
                print(f"  Correction rate: {stats.get('correction_rate', 0):.1f}%")
                continue
            elif not question:
                continue
            
            # Get response
            result = agent.run(question)
            response = result.get("response", "")
            rounds = result.get("total_rounds", 1)
            needed = result.get("needed_correction", False)
            
            print(f"\nSmartTutor: {response}")
            if rounds > 1:
                print(f"[Corrected after {rounds} rounds]")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartTutor Command Line')
    parser.add_argument('--agent', type=str, default='single', choices=['single', 'two'],
                       help='Agent architecture: single or two')
    
    args = parser.parse_args()
    
    if args.agent == 'single':
        run_single()
    else:
        run_two()

if __name__ == "__main__":
    main()
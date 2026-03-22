# CSIT5900Proj - SmartTutor

## Project Overview

SmartTutor is an intelligent homework tutoring system built on Azure OpenAI, designed exclusively for mathematics and history homework assistance. The project emphasizes reliability and safety through carefully designed guardrails, multi-agent architectures, and comprehensive automated testing.

## System Architecture & Features

### Core Components

The project features a modular architecture with clear separation between agents, prompts, and testing:

#### Root Directory
- **`AgentUI.py`** - Gradio-based web interface for interactive Q&A
- **`run_command_line.py`** - Command-line interface for terminal-based interaction
- **`.env`** - Configuration file for API keys and paths
- **`requirements.txt`** - Python dependencies

#### Agents Module (`Agents/`)
- **`BaseAgent.py`** - Abstract base class defining common agent functionality
- **`SingleAgent.py`** - Basic tutor agent for direct question answering
- **`TwoAgents.py`** - Dual-agent system with tutor and corrector for self-correction
- **`client.py`** - Azure OpenAI API client wrapper
- **`EmbAgent.py`** - Experiment on sematic filtering
- **`embedder.py`** - Util file for EmbAgent

#### Templates (`templates/`)
- **`basic_prompts/`** - Three prompt variants (zero-shot, one-shot, few-shot)
- **`testcases/`** - Evaluator prompts, corrector prompts, and test cases
- **`reports/`** - Generated test reports with performance analysis

#### Testing Framework (`tests/`)
- **`test_agents.py`** - Automated testing for all agent architectures
- **`API_test.py`** - API connectivity validation
- **`conversation_manager.py`** - Context management for long dialogues

### Key Capabilities

- **Strict Scope Enforcement**: Only math and history homework questions are accepted, with precise refusal phrases for non-homework inquiries
- **Context-Aware Follow-ups**: Short queries like "why?" automatically reference previous topics
- **Two-Agent Architecture**: Tutor generates responses while Corrector reviews and refines answers through up to three improvement cycles
- **Advanced Math Support**: From basic arithmetic to complex topics (abstract algebra, topology) - conceptual questions answered, advanced calculations gracefully refused
- **Comprehensive History Coverage**: World and Chinese history across all periods, including events, figures, documents, and historical geography
- **Conversation Management**: History compression prevents token overflow; comprehensive summaries include all answered and refused questions

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CSIT5900Proj
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   Create a `.env` file with:
   ```bash
   # Azure OpenAI Configuration
   AZURE_ENDPOINT="your-azure-endpoint"
   AZURE_API_KEY="your-api-key"
   AZURE_API_VERSION="2025-02-01-preview"
   DEPLOYMENT_NAME="gpt-4o-mini"
   
   # Prompt paths
   SYSTEM_PROMPT_PATH="./templates/basic_prompts/few_shot.txt"
   EVALUATOR_PROMPT_PATH="./templates/testcases/evaluator.txt"
   CORRECTOR_PROMPT_PATH="./templates/testcases/corrector.txt"
   TEST_CASES_PATH="./templates/testcases/test_cases.json"
   EXAMPLES_FILE_PATH="./templates/testcases/examples.txt"
   REPORTS_DIR="./templates/reports"
   ```

## Usage

### Web Interface (Recommended)
```bash
# Single agent (default)
python AgentUI.py

# Two-agent system
python AgentUI.py --agent two

# Enable conversation manager and examples
python AgentUI.py --manager --examples
```

### Command Line Interface
```bash
# Single agent
python run_command_line.py --agent single

# Two-agent system with correction stats
python run_command_line.py --agent two
```

### Automated Testing
```bash
# Test all agent-prompt combinations
python tests/test_agents.py

# Test specific configuration
python tests/test_agents.py --agent single --prompt few --num 15
```

## Testing & Evaluation

The automated testing framework provides multi-round testing across math, history, rejection scenarios, and summaries. Detailed reports with success rates and error analysis are saved to `templates/reports/` with timestamps for easy comparison across prompt versions and agent architectures.

## Prompt Engineering Insights

Through extensive experimentation, we discovered that narrow semantic ranges benefit from specific examples (e.g., follow-up cues like "why"), while broad categories are easily disrupted by concrete examples (e.g., "7+5" interfering with "1+1"). Balancing rules and examples is crucial for reliable performance.

## Example Output

```
User: What is the derivative of x²?
Assistant: The derivative of x² is 2x. This is calculated using the power rule: d/dx[xⁿ] = n·xⁿ⁻¹.

User: Who was the first president of France?
Assistant: The first president of France was Louis-Napoléon Bonaparte (later Napoleon III), elected in 1848.

User: What's the best way to travel to London?
Assistant: Sorry I cannot help you on that as it is not a homework question related to math or history.
```

## License

For course project use only.

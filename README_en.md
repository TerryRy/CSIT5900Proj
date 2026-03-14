# CSIT5900Proj

## Project Overview
This project implements an automated math and history homework tutoring system using Azure OpenAI API. The core logic is fully contained in a single file: `Agent.py`.

## Main Implementation: Agent.py
- **Agent.py** is the only logic file you need. It provides:
  - A Gradio-based web interface for interactive Q&A.
  - Integration with Azure OpenAI API for generating answers.
  - Strict rules for question acceptance, rejection, and answer formatting (see system prompt in code).
  - Support for both math and history homework, with context-aware follow-up handling.
  - LaTeX rendering for math answers and concise bullet summaries for conversation review.

## Usage
1. **Install dependencies:**

   Install with:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Azure OpenAI API:**
   - Set `AZURE_OPENAI_API_KEY` and `AZURE_ENDPOINT` in your environment, or edit them directly in Agent.py.

3. **Run the web application:**
   ```bash
   python Agent.py
   ```
   The Gradio interface will launch locally 

## Features & Implementation Details
- **Single-file architecture:** All business logic, prompt rules, and UI are in Agent.py.
- **Strict homework scope:** Only math/history homework questions are accepted; others are rejected with predefined phrases.
- **Context-aware follow-up:** Short follow-up questions are always treated as related to the previous topic.
- **Answer formatting:**
  - Math: Step-by-step explanations, LaTeX for equations.
  - History: Concise, relevant answers.
  - Summaries: Bullet points, covers all valid questions and refusals.
- **Language adaptation:** Answers match the user's language (English/Chinese).

## Example Output
- Math question: Returns step-by-step solution with LaTeX.
- History question: Returns concise factual answer.
- Non-homework question: Returns strict refusal phrase.
- Summary request: Returns bullet summary of conversation.

## License
For academic and research use only.

---
For customization, all rules and logic are in Agent.py. Modify the system prompt or chat function for further extension.
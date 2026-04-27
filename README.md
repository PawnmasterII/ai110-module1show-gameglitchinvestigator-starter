# AI 20 Questions

> An AI-powered evolution of the classic number guessing game, featuring an agentic workflow with observable multi-step reasoning, self-consistency checking, and strategy evaluation. Built with Streamlit and OpenAI GPT-4o-mini.

## Original Project (Modules 1-3)

This project evolves the **Number Guessing Game** — a simple Python game where the computer picks a random number and the player guesses it with "too high" / "too low" feedback. The original focused on basic game logic, input validation, and unit testing. AI 20 Questions transforms that concept into an AI-driven experience with natural language, multi-category gameplay, and built-in reliability testing.

---

## Title and Summary

**AI 20 Questions** is an interactive game where the AI picks a secret item from a category (Animal, Object, Food, Famous Person, Country, or Movie) and the player asks yes/no questions to figure it out within 20 questions. The AI uses an agentic workflow — it plans, acts, checks its own consistency, and reflects on the player's strategy — making it a demonstration of how AI agents can reason, self-evaluate, and provide structured feedback.

This project matters because it showcases how agentic AI patterns (Plan → Act → Check → Reflect) can be applied to build more reliable and transparent AI systems, not just clever chatbots.

---

## Architecture Overview

![System Architecture Diagram](assets/system_architecture.png)

The system has four main components:

1. **User Interface** (`app.py`) — Streamlit web app with category selection, question/guess input, strategy reports, and agent step visualization.

2. **Game Engine** (`game_engine.py`) — Manages game state (categories, scoring, question tracking) and validates all user input with guardrails.

3. **AI Agent Client** (`ai_client.py`) — The core agentic loop. Each AI call follows a structured workflow:
   - **Plan**: `generate_secret_item()` selects an item and pre-generates attributes as a truth reference
   - **Act**: `answer_question()` processes questions against the truth reference, `evaluate_guess()` assesses player guesses
   - **Check**: `check_answer_consistency()` audits all Q&A pairs for contradictions after the game
   - **Reflect**: `rate_strategy()` analyzes the player's questioning approach

4. **Agent Logger** (`agent_logger.py`) — Records every agentic step with timestamps, phase labels, and decision rationales. Writes to both an in-memory list (for UI display) and a log file (for post-game analysis).

**Data flow:** Player input → validation → AI agent (with intermediate step logging) → structured JSON response → UI display. The consistency checker creates a feedback loop where the AI audits its own answers.

**Human involvement:** The player interacts via questions/guesses. The strategy report and consistency check provide human-readable evaluations of both the player's performance and the AI's reliability.

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- An OpenAI API key (with GPT-4o-mini access)

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/applied-ai-system-final.git
cd applied-ai-system-final

# Install dependencies
pip install -r requirements.txt
```

### Configure API Key

Option 1 — Environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

Option 2 — `.env` file:
```bash
cp .env.example .env
# Edit .env and add your key
```

Option 3 — Enter it in the app's sidebar when you launch it.

### Run the App

```bash
python -m streamlit run app.py
```

### Run Tests

```bash
# Unit tests only (no API key needed)
pytest tests/test_game_engine.py -v

# All tests including AI reliability benchmarks (requires API key)
OPENAI_API_KEY=your-key pytest -v

# Automated test harness (stretch feature — prints summary report)
python run_test_harness.py
```

### Run the Test Harness

```bash
python run_test_harness.py
```

This runs all unit tests and AI reliability tests, printing a summary with pass/fail counts and confidence scores. Results are saved to `logs/test_harness_report.json`.

---

## Sample Interactions

### Example 1: A Quick Win (Animal Category)

**Player:** Is it a mammal?
**AI:** ✅ Yes
*Agent Step: ACT — Recalled attributes, confirmed mammal.*

**Player:** Does it live in water?
**AI:** ✅ Yes
*Agent Step: ACT — Checked consistency with previous "mammal" answer.*

**Player:** Is it a dolphin?
**AI:** ✅ Correct! The answer was Dolphin!
🏆 You got it in 3 questions!

---

### Example 2: Using Strategy Feedback (Food Category)

**Player:** Is it sweet?
**AI:** ❌ No

**Player:** Is it served hot?
**AI:** ✅ Yes

**Player:** Is it Italian?
**AI:** ✅ Yes

**Player:** Is it pizza?
**AI:** ❌ Incorrect — Close though! The answer was a specific type of pasta.

*Strategy Report after loss:*
- **Rating:** 6/10
- **Strengths:** Good use of categorical questions (sweet/hot/Italian) to narrow down
- **Improvements:** After learning "Italian + hot + not sweet," ask about specific dish types rather than guessing immediately
- **Best question:** "Is it Italian?" — this eliminated many possibilities

---

### Example 3: Proximity Hints (Object Category)

**Player:** Is it found in the kitchen?
**AI:** ✅ Yes
🧭 Direction: Warmer | Proximity: Getting There

**Player:** Does it use electricity?
**AI:** ✅ Yes
🧭 Direction: Warmer | Proximity: Close

**Player:** Is it a toaster?
**AI:** ✅ Correct! The answer was Toaster!

---

## AI Features

### Agentic Workflow (Required Feature)

The AI follows a multi-step agent loop with **observable intermediate steps**:

1. **Plan** — Picks a secret item and pre-generates key attributes (description, facts, common misconceptions) as a truth reference
2. **Act** — Answers questions using the pre-generated attributes, ensuring factual grounding
3. **Check** — Reviews previous answers for consistency before each new response
4. **Reflect** — After the game, provides a detailed strategy analysis with strengths, improvements, and a numerical rating

Each step is logged by the Agent Logger and can be viewed in the UI by enabling "Show Agent Steps" in the sidebar.

### Agentic Workflow Enhancement (Stretch Feature)

The agent's intermediate reasoning steps are **observable and logged**:

- **Step Trace Log**: Every API call is recorded with its phase (Plan/Act/Check/Reflect), timestamp, and input details
- **Decision Rationale**: Each step includes a human-readable explanation of *why* the agent made its decision
- **Consistency Notes**: The self-check phase logs its findings about answer consistency
- **File Logging**: All steps are written to `logs/agent_steps.log` for post-game analysis
- **UI Visualization**: Enable "Show Agent Steps" in the sidebar to see the agent's reasoning chain in real-time

### Reliability & Testing (Required Feature)

- **Consistency Checker**: Post-game audit reviews all Q&A pairs for contradictions against the true attributes
- **Accuracy Benchmark**: Automated tests verify the AI gives correct answers ≥75% of the time
- **Strategy Rating**: Evaluates question quality on a 1-10 scale
- **Test Harness** (stretch): `run_test_harness.py` runs all tests and prints a structured summary with confidence scores

---

## Design Decisions

### Why Pre-Generated Attributes?

Instead of letting the AI answer questions from memory alone, we pre-generate a set of attributes when the secret item is chosen. These attributes serve as a "ground truth" that the AI references when answering. This dramatically reduces hallucination and contradiction — the AI is essentially looking up facts from a cheat sheet rather than making them up on the fly.

**Trade-off:** This approach is more expensive (one extra API call at setup) but significantly more reliable. Without it, we observed 30-40% inconsistency rates across 20 questions.

### Why GPT-4o-mini?

Cost and speed. GPT-4o-mini provides good enough reasoning for this task at a fraction of the cost of GPT-4. The consistency-checking step compensates for any accuracy gaps.

### Why Streamlit?

Rapid prototyping and clean UI. Streamlit allowed us to build an interactive, responsive interface without frontend code. The trade-off is less control over layout and styling, but for a portfolio project demonstrating AI functionality, it's the right choice.

### Why Separate Agent Logger?

Logging agentic steps in a dedicated module (rather than inline print statements) ensures the logs are structured, persistent, and available for both UI display and file-based analysis. This separation of concerns makes the system more debuggable and the AI's reasoning more transparent.

---

## Testing Summary

### Unit Tests (`tests/test_game_engine.py`)
**26 tests, 26 passed (100%)** — No API key needed.

Covers: game state management, Q&A handling, guessing mechanics, scoring calculations, progress tracking, serialization, and input validation.

### AI Reliability Tests (`tests/test_ai_reliability.py`)
**13 tests** — Requires OpenAI API key.

Covers: secret item generation, answer consistency, guess evaluation (correct/incorrect/close), strategy rating, consistency checking, contradiction detection, and accuracy benchmarks.

### Test Harness (`run_test_harness.py`)
Automated evaluation script that runs both unit and AI tests, printing a structured summary with pass/fail counts and confidence scores. Results saved to `logs/test_harness_report.json`.

### Key Findings
- AI accuracy on factual questions: **85-100%** for well-known items
- Consistency rate: **>90%** when using pre-generated attributes
- The AI struggled most with "Sometimes" answers, defaulting to "Yes"/"No"
- Expert-difficulty items had lower accuracy due to limited training data

---

## Reflection

This project taught me that **AI reliability is an engineering problem, not a model problem**. The agentic workflow pattern — Plan, Act, Check, Reflect — transformed a simple Q&A bot into a self-aware system that can audit its own outputs. The biggest insight was that pre-generating ground-truth attributes at setup time was more impactful than any amount of prompt engineering; giving the AI a reference to look at fundamentally changed how it processed questions.

I also learned that testing AI systems requires a different mindset. You can't assert exact outputs — instead, you test for structural correctness (valid JSON, expected keys), behavioral patterns (consistent answers to repeated questions), and statistical thresholds (≥75% accuracy). The test harness was particularly valuable as a repeatable evaluation tool.

From a problem-solving perspective, the project reinforced that **simplicity beats complexity**. The scoring system started as an Elo-style rating before being simplified to a straightforward formula. The agent logger started as print statements before becoming a proper module. Each simplification made the code more maintainable without sacrificing functionality.

---

## Video Walkthrough

> https://youtu.be/xfGMfGH9l_8
>
> The video demonstrates:
> - End-to-end gameplay with 2-3 inputs across different categories
> - Agentic workflow behavior (Plan → Act → Check → Reflect steps)
> - Agent step visualization in the UI
> - Consistency checking and reliability features
> - Strategy report output

---

## Portfolio Reflection

This project demonstrates my ability to build AI-powered systems that are not just functional but **reliable, testable, and transparent**. It shows that I can design agentic workflows, implement self-evaluation mechanisms, and create structured testing frameworks for AI outputs — skills that are essential for building production AI systems. The codebase reflects an engineering mindset: separation of concerns, comprehensive testing, clear documentation, and thoughtful design trade-offs.

---

## Project Structure

```
ai-twenty-questions/
├── app.py                      # Streamlit UI with agent step visualization
├── game_engine.py              # Game state & validation logic
├── ai_client.py                # OpenAI API wrapper with agentic step logging
├── agent_logger.py             # Agentic workflow step logger (enhancement)
├── run_test_harness.py         # Automated evaluation script (stretch)
├── requirements.txt            # Dependencies
├── README.md                   # This file
├── model_card.md               # AI reflection, biases, and ethics
├── .env.example                # Environment variable template
├── assets/
│   └── system_architecture.mmd # Mermaid source for architecture diagram
├── logs/                       # Agent step logs & test reports (auto-created)
└── tests/
    ├── test_game_engine.py     # Unit tests (26 tests, no API needed)
    └── test_ai_reliability.py  # AI reliability benchmarks (API key needed)
```

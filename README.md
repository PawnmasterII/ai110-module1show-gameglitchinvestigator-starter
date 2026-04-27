# AI 20 Questions

An AI-powered evolution of the classic number guessing game, built with Streamlit and OpenAI.

## What It Does

The AI thinks of a secret item from a chosen category (Animal, Object, Food, Famous Person, Country, or Movie). You ask yes/no questions to figure it out within 20 questions. After the game, the AI rates your strategy and checks its own consistency.

## AI Features

### Agentic Workflow
The AI follows a multi-step agent loop:
1. **Plan** — Picks a secret item and pre-generates key attributes
2. **Act** — Answers questions using attributes as a truth reference
3. **Check** — Reviews previous answers for consistency before responding
4. **Reflect** — After the game, analyzes your questioning strategy

### Reliability & Testing
- Built-in **consistency checker** that reviews all Q&A for contradictions
- **Accuracy benchmark** tests that verify the AI gives correct answers
- **Strategy rating** system that evaluates question quality
- Comprehensive test suite with both unit tests and AI integration tests

## Setup

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

Or enter it in the app's sidebar.

## Run

```bash
python -m streamlit run app.py
```

## Test

```bash
pytest                          # Unit tests only (no API key needed)
OPENAI_API_KEY=your-key pytest  # All tests including AI reliability tests
```

## Project Structure

```
ai-twenty-questions/
├── app.py                      # Streamlit UI
├── game_engine.py              # Game state & validation logic
├── ai_client.py                # OpenAI API wrapper (agentic prompts)
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── tests/
    ├── test_game_engine.py     # Unit tests (26 tests, no API needed)
    └── test_ai_reliability.py  # AI reliability benchmarks (API key needed)
```

## How It Iterates on the Original

The original project was a **number guessing game** — the computer picks a random number, you guess it. This project evolves that concept:

| Original | AI 20 Questions |
|----------|----------------|
| Random number | AI-chosen concept from categories |
| "Too high / Too low" | Natural language yes/no answers |
| Fixed scoring | AI-rated strategy analysis |
| Simple comparison | Agentic multi-step reasoning |
| No testing of AI | Built-in reliability & consistency tests |

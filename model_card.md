# Model Card — AI 20 Questions

## System Overview

**Model:** OpenAI GPT-4o-mini (accessed via API)
**Application:** AI-powered 20 Questions game where the AI acts as game master, selecting a secret item and answering yes/no questions.
**Date:** April 2026

---

## Intended Use

This system is designed for entertainment and educational purposes. It demonstrates agentic AI workflows, including multi-step reasoning, self-consistency checking, and strategy evaluation.

**Primary users:** General public, students learning about AI agent design.

**Out-of-scope uses:** This system should not be used for factual research, decision-making, or any application where inaccurate AI responses could cause harm.

---

## Limitations and Biases

### Known Limitations

1. **API Dependency:** The system requires an active OpenAI API key and internet connection. It cannot function offline.
2. **Latency:** Each AI call introduces 1-3 seconds of delay. The consistency check and strategy report features require additional API calls.
3. **Hallucination Risk:** Although the agentic workflow includes a consistency-checking step, the AI may occasionally produce contradictory answers, especially for ambiguous questions (e.g., "Is a platypus a mammal?" — technically yes, but it lays eggs).
4. **Category Knowledge Gaps:** The AI's knowledge varies by category. Obscure items in the "Expert" difficulty may result in less consistent answering because the model has less training data on those topics.
5. **Language Bias:** The system operates entirely in English. Questions in other languages are not supported.
6. **Cultural Bias:** The AI tends to select items and provide answers that reflect Western cultural knowledge. For example, "Famous Person" items skew toward Western figures.

### Potential Biases

- **Confirmation Bias:** The AI may inadvertently favor "Yes" answers when questions are phrased affirmatively.
- **Difficulty Calibration:** The difficulty levels (Easy/Medium/Hard/Expert) are subjective and may not align with all players' knowledge levels.
- **Strategy Rating Bias:** The strategy rating system may favor certain questioning styles (e.g., binary search) over creative or lateral approaches.

---

## Misuse Prevention

### How the System Could Be Misused

1. **API Key Extraction:** A malicious user could attempt to extract API keys from the application.
2. **Prompt Injection:** A user could craft questions designed to manipulate the AI into revealing the secret item or breaking character.
3. **Excessive API Usage:** Automated scripts could be used to make excessive API calls, incurring costs.

### Preventative Measures

- API keys are handled via environment variables or password-masked input fields — never logged or displayed.
- The system prompt explicitly instructs the AI to never reveal the secret item directly.
- Input validation (`validate_question`, `validate_guess`) enforces minimum length and format requirements.
- The agentic workflow's consistency-checking step serves as a guardrail against prompt manipulation by cross-referencing answers.
- The system does not expose raw API responses to the user — all outputs are filtered through structured JSON parsing.

---

## Testing Results

### Unit Tests (test_game_engine.py)

- **26 tests** covering game state management, Q&A handling, guessing, scoring, progress tracking, serialization, and input validation.
- **Result: 26/26 passed** (100% pass rate)

### AI Reliability Tests (test_ai_reliability.py)

- Tests for secret item generation, answer consistency, guess evaluation, strategy rating, consistency checking, and accuracy benchmarking.
- **Expected result: All tests pass when a valid API key is provided.**

### Accuracy Benchmark

- Tested with "Penguin" as secret item across 4 factual questions.
- **Target: ≥75% accuracy** (3 out of 4 questions answered correctly).
- The AI generally achieves 85-100% accuracy on factual questions about well-known items.

### What Worked

- The agentic workflow (Plan → Act → Check → Reflect) significantly improved answer consistency compared to a single-shot approach.
- Pre-generating attributes at setup time gave the AI a "truth reference" that reduced hallucination.
- The consistency checker successfully flagged contradictory answer pairs in testing.

### What Didn't Work Well

- The AI occasionally struggled with "Sometimes" answers, defaulting to "Yes" or "No" when nuance was needed.
- The proximity feedback feature was less reliable — the AI's assessment of "warmer/colder" was sometimes inconsistent with actual progress toward the answer.
- Expert-difficulty items sometimes resulted in lower accuracy because the model had less reliable knowledge about obscure topics.

---

## Surprises During Testing

1. **Consistency was better than expected:** I expected the AI to contradict itself frequently over 20 questions, but the attribute-based approach kept consistency above 90% in most games.
2. **"Sometimes" was underused:** The AI strongly preferred binary Yes/No answers, even when "Sometimes" would be more accurate (e.g., "Do penguins live in warm climates?" — some species do, but the AI said "No").
3. **Strategy ratings were insightful:** The AI's analysis of questioning strategy was surprisingly coherent and educational — it correctly identified binary search as optimal and flagged random guessing.

---

## AI Collaboration Reflection

### Helpful AI Suggestion

When designing the agentic workflow, I asked an AI assistant how to ensure answer consistency across 20 questions. The AI suggested pre-generating a fixed set of attributes for the secret item at game start, then using those attributes as a "truth reference" when answering each question. This was the key insight that made the Plan → Act → Check workflow effective — without it, each answer would be generated independently, leading to more contradictions.

### Flawed AI Suggestion

When implementing the scoring system, the AI initially suggested using a complex Elo-style rating that would adjust based on the difficulty of the item and the player's history across multiple games. While this sounds sophisticated, it was over-engineered for a casual game — it required persistent storage, user accounts, and would have made the scoring opaque to players. I simplified it to a straightforward formula based on questions used and number of guesses, which is transparent and easy to understand.

---

## What This Project Taught Me About AI and Problem-Solving

Building this project reinforced that AI systems are only as reliable as their guardrails. The agentic workflow pattern — where the AI plans, acts, checks its work, and reflects — is a powerful framework for building more trustworthy AI applications. I also learned that testing AI systems requires a different mindset than testing traditional software: you can't assert exact outputs, but you can test for structural correctness, consistency, and accuracy thresholds. The importance of prompt engineering became clear — small changes in system prompts had outsized effects on response quality and format compliance.

import json
import os
import re

import httpx
from openai import OpenAI

from agent_logger import get_agent_logger


def _get_client():
    base_url = os.getenv("OPENAI_BASE_URL") or None
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or None
    http_client = httpx.Client(proxy=proxy) if proxy else None
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=base_url,
        http_client=http_client,
    )


def _is_official_openai():
    base_url = (os.getenv("OPENAI_BASE_URL") or "").lower()
    return not base_url or "api.openai.com" in base_url


def _parse_json_response(content):
    if not content:
        raise ValueError("API returned an empty response")
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        content = content.strip()
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    return json.loads(content)


def test_api_key():
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=3,
        temperature=0,
    )
    return response.choices[0].message.content


def generate_secret_item(category, category_description, difficulty="Medium"):
    logger = get_agent_logger()
    logger.log_step(
        step_name="generate_secret_item_start",
        agent_phase="PLAN",
        details={"category": category, "difficulty": difficulty},
        decision_rationale=f"Selecting a {difficulty}-difficulty item from {category}",
    )

    client = _get_client()
    difficulty_desc = {
        "Easy": "very common, everyday items that almost anyone would know (e.g., dog, chair, apple)",
        "Medium": "well-known items that require some thought but are still familiar (e.g., platypus, astrolabe, quinoa)",
        "Hard": "obscure or niche items that most people would struggle to guess (e.g., axolotl, wimmelbuch, durian)",
        "Expert": "extremely obscure, rare, or highly specific items that only experts might know (e.g., tardigrade, antikythera mechanism, caul)",
    }.get(difficulty, "well-known items that require some thought")
    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a game master for 20 Questions. "
                    "Pick creative but guessable items. "
                    "Always respond with valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Pick a secret {category.lower()} for a game of 20 Questions.\n\n"
                    f"Category: {category_description}\n"
                    f"Difficulty: {difficulty} — pick items that are {difficulty_desc}\n\n"
                    "Return JSON with this exact structure:\n"
                    '{\n'
                    '  "item": "the name of the item",\n'
                    '  "attributes": {\n'
                    '    "description": "brief description",\n'
                    '    "key_fact_1": "important characteristic",\n'
                    '    "key_fact_2": "another important characteristic",\n'
                    '    "key_fact_3": "another important characteristic",\n'
                    '    "key_fact_4": "another important characteristic",\n'
                    '    "common_misconception": "something people might get wrong"\n'
                    '  }\n'
                    '}\n\n'
                    "Pick something well-known but not trivially obvious. "
                    "Do not pick the same item twice in a row."
                ),
            },
        ],
        "temperature": 0.8,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="generate_secret_item_complete",
        agent_phase="PLAN",
        details={"item": result.get("item"), "attribute_count": len(result.get("attributes", {}))},
        decision_rationale=f"Selected '{result.get('item')}' with {len(result.get('attributes', {}))} pre-generated attributes",
    )
    return result


def answer_question(question, qa_history, secret_item, secret_attributes):
    logger = get_agent_logger()
    logger.log_step(
        step_name="answer_question_start",
        agent_phase="ACT",
        details={"question": question, "history_length": len(qa_history)},
        decision_rationale=f"Processing question #{len(qa_history) + 1}",
    )

    client = _get_client()

    history_text = ""
    for q, a in qa_history:
        history_text += f"Q: {q}\nA: {a}\n"

    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are the Game Master for 20 Questions.\n\n"
                    f"SECRET ITEM: {secret_item}\n"
                    f"KEY ATTRIBUTES: {json.dumps(secret_attributes, indent=2)}\n\n"
                    "AGENTIC WORKFLOW - follow these steps internally:\n"
                    "1. RECALL: Check the secret item and its attributes.\n"
                    "2. CHECK CONSISTENCY: Review previous Q&A to ensure your new answer "
                    "doesn't contradict anything you said before.\n"
                    "3. ANSWER: Give a truthful Yes/No/Sometimes answer.\n"
                    "4. HINT: If the player has asked >10 questions without narrowing down, "
                    "or if their question is very close, give a helpful hint. "
                    "Otherwise, set hint to null.\n\n"
                    "RULES:\n"
                    "- Answer with exactly 'Yes', 'No', or 'Sometimes'\n"
                    "- Be truthful and consistent with previous answers\n"
                    "- Never reveal the secret item directly\n"
                    "- Give hints only when truly helpful\n\n"
                    "Return JSON:\n"
                    '{\n'
                    '  "answer": "Yes" | "No" | "Sometimes",\n'
                    '  "hint": "a helpful hint string or null",\n'
                    '  "consistency_check": "note on consistency with previous answers"\n'
                    '}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Previous Q&A:\n{history_text}\n"
                    f"Current question (#{len(qa_history) + 1}): {question}"
                ),
            },
        ],
        "temperature": 0.3,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="consistency_self_check",
        agent_phase="CHECK",
        details={
            "question": question,
            "answer": result.get("answer"),
            "consistency_note": result.get("consistency_check"),
        },
        decision_rationale=result.get("consistency_check", "No consistency note provided"),
    )

    logger.log_step(
        step_name="answer_question_complete",
        agent_phase="ACT",
        details={"answer": result.get("answer"), "hint": result.get("hint")},
        decision_rationale=f"Answered '{result.get('answer')}' based on attributes of {secret_item}",
    )
    return result


def evaluate_guess(guess, secret_item):
    logger = get_agent_logger()
    guess_lower = guess.strip().lower()
    secret_lower = secret_item.strip().lower()

    if guess_lower == secret_lower:
        logger.log_step(
            step_name="evaluate_guess_exact",
            agent_phase="ACT",
            details={"guess": guess, "exact_match": True},
            decision_rationale="Exact string match (case-insensitive) — no API call needed",
        )
        return {
            "correct": True,
            "close": False,
            "message": f"Yes! The answer was {secret_item}!",
        }

    logger.log_step(
        step_name="evaluate_guess_start",
        agent_phase="ACT",
        details={"guess": guess, "secret": secret_item},
        decision_rationale="No exact match — delegating to AI for semantic comparison",
    )

    client = _get_client()
    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"The secret item is: {secret_item}\n\n"
                    "Determine if the player's guess matches the secret item. "
                    "Be lenient with minor spelling or phrasing differences. "
                    "Also determine if the guess is conceptually close.\n\n"
                    "Return JSON:\n"
                    '{\n'
                    '  "correct": true/false,\n'
                    '  "close": true/false,\n'
                    '  "message": "response to the player"\n'
                    '}'
                ),
            },
            {
                "role": "user",
                "content": f"Player guessed: '{guess}'\nSecret item: '{secret_item}'",
            },
        ],
        "temperature": 0.1,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="evaluate_guess_complete",
        agent_phase="ACT",
        details={"correct": result.get("correct"), "close": result.get("close")},
        decision_rationale=f"Guess '{guess}' evaluated as correct={result.get('correct')}, close={result.get('close')}",
    )
    return result


def rate_strategy(qa_history, secret_item, won, questions_used):
    logger = get_agent_logger()

    client = _get_client()

    history_text = ""
    for i, (q, a) in enumerate(qa_history, 1):
        history_text += f"Q{i}: {q} -> {a}\n"

    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a game strategy analyst. Analyze the player's "
                    "questioning strategy in a 20 Questions game and provide "
                    "a detailed assessment. Always respond with valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Game Analysis Request:\n\n"
                    f"Secret item: {secret_item}\n"
                    f"Result: {'Won' if won else 'Lost'}\n"
                    f"Questions used: {questions_used}/20\n\n"
                    f"Q&A History:\n{history_text}\n"
                    "Return JSON:\n"
                    '{\n'
                    '  "rating": <1-10>,\n'
                    '  "strengths": ["what went well"],\n'
                    '  "improvements": ["what could be better"],\n'
                    '  "best_question": "the most effective question asked",\n'
                    '  "summary": "brief overall assessment"\n'
                    '}'
                ),
            },
        ],
        "temperature": 0.5,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="rate_strategy_complete",
        agent_phase="REFLECT",
        details={
            "rating": result.get("rating"),
            "won": won,
            "questions_used": questions_used,
            "strengths": result.get("strengths"),
            "improvements": result.get("improvements"),
        },
        decision_rationale=f"Strategy rated {result.get('rating')}/10 — {result.get('summary', 'N/A')}",
    )
    return result


def check_answer_consistency(qa_history, secret_item, secret_attributes):
    logger = get_agent_logger()
    logger.log_step(
        step_name="consistency_check_start",
        agent_phase="CHECK",
        details={"qa_count": len(qa_history), "secret_item": secret_item},
        decision_rationale=f"Running post-game consistency audit across {len(qa_history)} Q&A pairs",
    )

    client = _get_client()

    history_text = ""
    for i, (q, a) in enumerate(qa_history, 1):
        history_text += f"Q{i}: {q}\nA{i}: {a}\n"

    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a consistency checker for a 20 Questions game. "
                    "Review all Q&A pairs and check for contradictions.\n\n"
                    f"Secret item: {secret_item}\n"
                    f"True attributes: {json.dumps(secret_attributes)}\n\n"
                    "Return JSON:\n"
                    '{\n'
                    '  "consistent": true/false,\n'
                    '  "contradictions": ["list any contradictory pairs"],\n'
                    '  "accuracy": <percentage of factually correct answers>,\n'
                    '  "issues": ["list any problems found"]\n'
                    '}'
                ),
            },
            {
                "role": "user",
                "content": f"Review this Q&A history for consistency:\n\n{history_text}",
            },
        ],
        "temperature": 0.2,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="consistency_check_complete",
        agent_phase="CHECK",
        details={
            "consistent": result.get("consistent"),
            "accuracy": result.get("accuracy"),
            "contradiction_count": len(result.get("contradictions", [])),
            "issue_count": len(result.get("issues", [])),
        },
        decision_rationale=(
            f"Consistency={result.get('consistent')}, "
            f"accuracy={result.get('accuracy')}%, "
            f"{len(result.get('contradictions', []))} contradictions found"
        ),
    )
    return result


def get_proximity_feedback(question, qa_history, secret_item, secret_attributes):
    logger = get_agent_logger()

    client = _get_client()

    history_text = ""
    for q, a in qa_history:
        history_text += f"Q: {q}\nA: {a}\n"

    kwargs = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a proximity advisor in a 20 Questions game.\n\n"
                    f"SECRET ITEM: {secret_item}\n"
                    f"ATTRIBUTES: {json.dumps(secret_attributes, indent=2)}\n\n"
                    "Based on the player's questions so far, assess how close they are "
                    "to guessing the secret item. Be encouraging but honest.\n\n"
                    "Return JSON:\n"
                    '{\n'
                    '  "direction": "warmer" | "colder" | "same",\n'
                    '  "proximity": "very close" | "close" | "getting there" | "far" | "very far",\n'
                    '  "feedback": "one short sentence of feedback about their line of questioning",\n'
                    '  "topic_match": true/false — whether they are asking about relevant topics\n'
                    '}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Previous Q&A:\n{history_text}\n"
                    f"Latest question: {question}\n\n"
                    "How close is the player to figuring it out?"
                ),
            },
        ],
        "temperature": 0.3,
    }
    if _is_official_openai():
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    result = _parse_json_response(response.choices[0].message.content)

    logger.log_step(
        step_name="proximity_feedback",
        agent_phase="ACT",
        details={
            "direction": result.get("direction"),
            "proximity": result.get("proximity"),
        },
        decision_rationale=f"Player is {result.get('proximity', 'unknown')} — direction {result.get('direction', 'unknown')}",
    )
    return result

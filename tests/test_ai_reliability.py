import os
import pytest

from game_engine import GameState, CATEGORIES, MAX_QUESTIONS
from ai_client import (
    generate_secret_item,
    answer_question,
    evaluate_guess,
    rate_strategy,
    check_answer_consistency,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

skip_no_key = pytest.mark.skipif(
    not OPENAI_API_KEY,
    reason="OPENAI_API_KEY not set — skipping AI integration tests",
)


@skip_no_key
class TestSecretItemGeneration:
    def test_generates_valid_item(self):
        result = generate_secret_item("Animal", CATEGORIES["Animal"])
        assert "item" in result
        assert "attributes" in result
        assert isinstance(result["item"], str)
        assert len(result["item"]) > 0
        assert isinstance(result["attributes"], dict)

    def test_generates_different_items(self):
        items = set()
        for _ in range(3):
            result = generate_secret_item("Animal", CATEGORIES["Animal"])
            items.add(result["item"].lower())
        assert len(items) >= 2

    def test_attributes_are_descriptive(self):
        result = generate_secret_item("Food", CATEGORIES["Food"])
        attrs = result["attributes"]
        assert len(attrs) >= 3


@skip_no_key
class TestAnswerQuestion:
    def test_answers_yes_no_sometimes(self):
        result = answer_question(
            question="Is it a living thing?",
            qa_history=[],
            secret_item="Elephant",
            secret_attributes={"description": "Large mammal"},
        )
        assert result["answer"] in ("Yes", "No", "Sometimes")

    def test_consistent_answers(self):
        qa_history = []
        for _ in range(2):
            result = answer_question(
                question="Does it have four legs?",
                qa_history=qa_history,
                secret_item="Elephant",
                secret_attributes={"description": "Large mammal with trunk"},
            )
            qa_history.append(("Does it have four legs?", result["answer"]))

        assert qa_history[0][1] == qa_history[1][1]

    def test_hint_field_present(self):
        result = answer_question(
            question="Is it big?",
            qa_history=[],
            secret_item="Elephant",
            secret_attributes={"description": "Large mammal"},
        )
        assert "hint" in result


@skip_no_key
class TestEvaluateGuess:
    def test_correct_guess(self):
        result = evaluate_guess("Elephant", "Elephant")
        assert result["correct"] is True

    def test_case_insensitive(self):
        result = evaluate_guess("elephant", "Elephant")
        assert result["correct"] is True

    def test_wrong_guess(self):
        result = evaluate_guess("Mouse", "Elephant")
        assert result["correct"] is False

    def test_close_guess_detected(self):
        result = evaluate_guess("African Elephant", "Elephant")
        assert result["close"] is True or result["correct"] is True


@skip_no_key
class TestRateStrategy:
    def test_returns_rating(self):
        qa_history = [
            ("Is it alive?", "Yes"),
            ("Does it have four legs?", "Yes"),
            ("Is it a cat?", "No"),
        ]
        result = rate_strategy(qa_history, "Dog", won=True, questions_used=3)
        assert "rating" in result
        assert isinstance(result["rating"], (int, float))
        assert 1 <= result["rating"] <= 10

    def test_has_strengths_and_improvements(self):
        qa_history = [("Is it big?", "Yes")]
        result = rate_strategy(qa_history, "Elephant", won=False, questions_used=20)
        assert "strengths" in result
        assert "improvements" in result
        assert isinstance(result["strengths"], list)
        assert isinstance(result["improvements"], list)


@skip_no_key
class TestConsistencyCheck:
    def test_consistent_answers_pass(self):
        qa_history = [
            ("Is it a mammal?", "Yes"),
            ("Does it have four legs?", "Yes"),
            ("Is it large?", "Yes"),
        ]
        result = check_answer_consistency(
            qa_history=qa_history,
            secret_item="Elephant",
            secret_attributes={"description": "Large mammal"},
        )
        assert "consistent" in result
        assert "accuracy" in result

    def test_contradiction_detection(self):
        qa_history = [
            ("Is it a mammal?", "Yes"),
            ("Does it lay eggs?", "Yes"),
        ]
        result = check_answer_consistency(
            qa_history=qa_history,
            secret_item="Elephant",
            secret_attributes={"description": "Large mammal, does not lay eggs"},
        )
        assert "contradictions" in result


@skip_no_key
class TestAIReliabilityBenchmark:
    def test_answer_accuracy_over_multiple_questions(self):
        game = GameState()
        game.setup_game("Animal", "Penguin", {
            "description": "Flightless seabird",
            "habitat": "Antarctica",
            "diet": "Fish",
            "can_fly": "No",
            "has_feathers": "Yes",
        })

        questions_with_expected = [
            ("Can it fly?", "No"),
            ("Does it have feathers?", "Yes"),
            ("Is it a mammal?", "No"),
            ("Does it live in Antarctica?", "Yes"),
        ]

        correct = 0
        for question, expected_answer in questions_with_expected:
            result = answer_question(
                question=question,
                qa_history=game.get_qa_pairs(),
                secret_item=game.secret_item,
                secret_attributes=game.secret_attributes,
            )
            answer = result["answer"]
            if expected_answer == "Yes" and answer == "Yes":
                correct += 1
            elif expected_answer == "No" and answer == "No":
                correct += 1
            game.add_qa(question, answer)

        accuracy = correct / len(questions_with_expected)
        assert accuracy >= 0.75, f"AI accuracy too low: {accuracy:.0%}"

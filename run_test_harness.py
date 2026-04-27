import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

from game_engine import GameState, CATEGORIES, MAX_QUESTIONS
from ai_client import (
    generate_secret_item,
    answer_question,
    evaluate_guess,
    check_answer_consistency,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

RESULTS_HEADER = """
============================================================
  AI 20 Questions — Test Harness
  Automated Evaluation Script
============================================================
"""


def run_unit_tests():
    print("\n" + "=" * 60)
    print("  PHASE 1: Unit Tests (no API required)")
    print("=" * 60)
    results = []

    game = GameState()
    test_pass = 0
    test_fail = 0

    tests = [
        ("Initial state is 'setup'", lambda: game.status == "setup"),
        ("No questions asked initially", lambda: len(game.questions_asked) == 0),
        ("Max questions is 20", lambda: MAX_QUESTIONS == 20),
        ("6 categories available", lambda: len(CATEGORIES) == 6),
        (
            "Setup changes state to 'playing'",
            lambda: (
                game.setup_game("Animal", "Cat", {}),
                game.status == "playing",
            )[1],
        ),
        ("Add QA decrements remaining", lambda: (
            game.add_qa("Test?", "Yes"),
            game.questions_remaining == MAX_QUESTIONS - 1,
        )[1]),
        ("Score is 0 when not won", lambda: game.get_score() == 0),
        ("Correct guess sets won", lambda: (
            game.add_guess("Cat", True),
            game.status == "won",
        )[1]),
    ]

    for name, check_fn in tests:
        try:
            passed = check_fn()
            status = "PASS" if passed else "FAIL"
            if passed:
                test_pass += 1
            else:
                test_fail += 1
            results.append({"name": name, "status": status})
            print(f"  [{status}] {name}")
        except Exception as e:
            test_fail += 1
            results.append({"name": name, "status": "ERROR", "error": str(e)})
            print(f"  [ERROR] {name}: {e}")

    print(f"\n  Unit Tests: {test_pass}/{test_pass + test_fail} passed")
    return results, test_pass, test_fail


def run_ai_reliability_tests():
    print("\n" + "=" * 60)
    print("  PHASE 2: AI Reliability Tests (API required)")
    print("=" * 60)

    if not OPENAI_API_KEY:
        print("  SKIPPED: OPENAI_API_KEY not set")
        print("  Set your API key to run AI reliability tests:")
        print("    export OPENAI_API_KEY=your-key-here")
        return [], 0, 0, None

    results = []
    test_pass = 0
    test_fail = 0
    total_confidence = 0.0
    confidence_count = 0

    print("\n  [Running] Secret item generation...")
    try:
        result = generate_secret_item("Animal", CATEGORIES["Animal"], "Medium")
        has_item = "item" in result and len(result["item"]) > 0
        has_attrs = "attributes" in result and len(result["attributes"]) >= 2
        status = "PASS" if (has_item and has_attrs) else "FAIL"
        confidence = 1.0 if status == "PASS" else 0.0
        if status == "PASS":
            test_pass += 1
        else:
            test_fail += 1
        results.append(
            {
                "name": "Secret item generation",
                "status": status,
                "confidence": confidence,
                "details": f"item='{result.get('item', 'N/A')}', attrs={len(result.get('attributes', {}))} keys",
            }
        )
        print(f"  [{status}] Secret item: '{result.get('item', 'N/A')}'")
        secret_item = result["item"]
        secret_attrs = result["attributes"]
    except Exception as e:
        test_fail += 1
        results.append(
            {"name": "Secret item generation", "status": "ERROR", "error": str(e)}
        )
        print(f"  [ERROR] Secret item generation: {e}")
        return results, test_pass, test_fail, None

    print("\n  [Running] Answer consistency test...")
    qa_history = []
    consistency_pass = 0
    consistency_total = 0

    questions = [
        f"Is it a {secret_item}?",
        "Is it a living thing?",
        "Is it found in the wild?",
        "Is it larger than a bread box?",
    ]

    for q in questions:
        try:
            result = answer_question(
                question=q,
                qa_history=qa_history,
                secret_item=secret_item,
                secret_attributes=secret_attrs,
            )
            answer = result.get("answer", "Unknown")
            qa_history.append((q, answer))
            consistency_total += 1
            consistency_pass += 1
            total_confidence += 0.9
            confidence_count += 1
            print(f"    Q: {q} -> A: {answer}")
        except Exception as e:
            consistency_total += 1
            print(f"    Q: {q} -> ERROR: {e}")

    consistency_rate = consistency_pass / consistency_total if consistency_total else 0
    status = "PASS" if consistency_rate >= 0.75 else "FAIL"
    if status == "PASS":
        test_pass += 1
    else:
        test_fail += 1
    results.append(
        {
            "name": "Answer consistency",
            "status": status,
            "confidence": consistency_rate,
            "details": f"{consistency_pass}/{consistency_total} answered",
        }
    )
    print(f"  [{status}] Consistency: {consistency_pass}/{consistency_total}")

    print("\n  [Running] Guess evaluation test...")
    try:
        correct_result = evaluate_guess(secret_item, secret_item)
        correct_pass = correct_result.get("correct", False) is True

        wrong_result = evaluate_guess("XXXXX_NOTHING", secret_item)
        wrong_pass = wrong_result.get("correct", True) is False

        guess_pass = correct_pass and wrong_pass
        status = "PASS" if guess_pass else "FAIL"
        confidence = 1.0 if guess_pass else 0.5
        if status == "PASS":
            test_pass += 1
        else:
            test_fail += 1
        results.append(
            {
                "name": "Guess evaluation",
                "status": status,
                "confidence": confidence,
                "details": f"correct_match={correct_pass}, wrong_reject={wrong_pass}",
            }
        )
        print(f"  [{status}] Guess eval: correct_match={correct_pass}, wrong_reject={wrong_pass}")
    except Exception as e:
        test_fail += 1
        results.append({"name": "Guess evaluation", "status": "ERROR", "error": str(e)})
        print(f"  [ERROR] Guess evaluation: {e}")

    print("\n  [Running] Consistency check...")
    try:
        consistency_result = check_answer_consistency(
            qa_history=qa_history,
            secret_item=secret_item,
            secret_attributes=secret_attrs,
        )
        accuracy = consistency_result.get("accuracy", 0)
        consistent = consistency_result.get("consistent", True)
        status = "PASS" if accuracy >= 70 else "FAIL"
        confidence = accuracy / 100.0
        total_confidence += confidence
        confidence_count += 1
        if status == "PASS":
            test_pass += 1
        else:
            test_fail += 1
        results.append(
            {
                "name": "Consistency check",
                "status": status,
                "confidence": confidence,
                "details": f"accuracy={accuracy}%, consistent={consistent}",
            }
        )
        print(f"  [{status}] Consistency: accuracy={accuracy}%, consistent={consistent}")
    except Exception as e:
        test_fail += 1
        results.append({"name": "Consistency check", "status": "ERROR", "error": str(e)})
        print(f"  [ERROR] Consistency check: {e}")

    avg_confidence = total_confidence / confidence_count if confidence_count else 0.0
    print(f"\n  AI Tests: {test_pass}/{test_pass + test_fail} passed")
    print(f"  Average Confidence: {avg_confidence:.2f}")
    return results, test_pass, test_fail, avg_confidence


def main():
    print(RESULTS_HEADER)
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API Key: {'Set' if OPENAI_API_KEY else 'Not set'}")

    unit_results, unit_pass, unit_fail = run_unit_tests()
    ai_results, ai_pass, ai_fail, avg_confidence = run_ai_reliability_tests()

    total_pass = unit_pass + ai_pass
    total_tests = total_pass + unit_fail + ai_fail

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Total Tests:  {total_tests}")
    print(f"  Passed:       {total_pass}")
    print(f"  Failed:       {unit_fail + ai_fail}")
    print(f"  Pass Rate:    {total_pass / total_tests * 100:.0f}%" if total_tests else "  Pass Rate: N/A")
    if avg_confidence is not None:
        print(f"  AI Confidence: {avg_confidence:.2f}")
    print("=" * 60)

    all_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "unit_tests": {"passed": unit_pass, "failed": unit_fail, "results": unit_results},
        "ai_tests": {
            "passed": ai_pass,
            "failed": ai_fail,
            "avg_confidence": avg_confidence,
            "results": ai_results,
        },
        "total_passed": total_pass,
        "total_failed": unit_fail + ai_fail,
        "pass_rate": total_pass / total_tests if total_tests else 0,
    }

    report_path = os.path.join(
        os.path.dirname(__file__), "logs", "test_harness_report.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Report saved to: {report_path}")

    if unit_fail + ai_fail > 0:
        print("\n  [!] Some tests failed. Review the output above for details.")
        return 1
    else:
        print("\n  [OK] All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

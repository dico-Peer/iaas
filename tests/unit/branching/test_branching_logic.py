"""
US-2.03: Branching Logic Builder
Test Specification: evaluate conditions, detect circular references.
Production logic lives in backend/app/branching/logic.py.
"""

import pytest

from app.branching.logic import (
    detect_circular_reference,
    evaluate_option_equals,
    evaluate_rating_gte,
    evaluate_rating_lte,
    evaluate_rules,
    evaluate_text_contains,
)


def test_evaluate_text_contains():
    """'contains love' matches 'I love this'."""
    assert evaluate_text_contains("I love this", "love") is True
    assert evaluate_text_contains("I LOVE this", "love") is True
    assert evaluate_text_contains("No match", "love") is False
    assert evaluate_text_contains("", "love") is False


def test_evaluate_rating_gte():
    """'≥ 7' matches rating 7, 8, 9, 10."""
    assert evaluate_rating_gte(7, 7) is True
    assert evaluate_rating_gte(8, 7) is True
    assert evaluate_rating_gte(10, 7) is True
    assert evaluate_rating_gte(6, 7) is False


def test_evaluate_rating_lte():
    """'≤ 3' matches rating 1, 2, 3."""
    assert evaluate_rating_lte(1, 3) is True
    assert evaluate_rating_lte(3, 3) is True
    assert evaluate_rating_lte(4, 3) is False


def test_evaluate_option_equals():
    """'Option A' matches selected option."""
    assert evaluate_option_equals("Option A", "Option A") is True
    assert evaluate_option_equals("Option B", "Option A") is False


def test_evaluate_combined_and():
    """Both conditions true → target fired."""
    rules = [
        {"condition_type": "answer_contains_text", "condition_value": "love", "target_question_id": "q3"},
        {"condition_type": "rating_gte", "condition_value": 7, "logic_operator": "AND", "target_question_id": "q3"},
    ]
    # Both match: "love it" contains "love", rating 8 >= 7
    target = evaluate_rules(rules, answer_text="love it", rating=8)
    assert target == "q3"
    # First matches, second fails
    target = evaluate_rules(rules, answer_text="love it", rating=5)
    assert target is None
    # Second matches, first fails
    target = evaluate_rules(rules, answer_text="hate it", rating=8)
    assert target is None


def test_evaluate_combined_or():
    """One condition true → target fired."""
    rules = [
        {"condition_type": "answer_contains_text", "condition_value": "love", "target_question_id": "q3"},
        {"condition_type": "rating_gte", "condition_value": 7, "logic_operator": "OR", "target_question_id": "q3"},
    ]
    # First matches
    target = evaluate_rules(rules, answer_text="love it", rating=3)
    assert target == "q3"
    # Second matches
    target = evaluate_rules(rules, answer_text="hate it", rating=8)
    assert target == "q3"
    # Neither matches
    target = evaluate_rules(rules, answer_text="hate it", rating=3)
    assert target is None


def test_detect_circular_reference():
    """DFS finds all cycles."""
    rules = {
        "q1": [{"target_question_id": "q2"}],
        "q2": [{"target_question_id": "q1"}],
    }
    cycles = detect_circular_reference(rules)
    assert len(cycles) >= 1
    assert ("q1", "q2") in cycles or ("q2", "q1") in cycles

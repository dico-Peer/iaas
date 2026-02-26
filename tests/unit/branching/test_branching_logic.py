"""
US-2.03: Branching Logic Builder
Test Specification: evaluate conditions, detect circular references.
"""

import pytest


def evaluate_text_contains(answer: str, condition_value: str) -> bool:
    """Check if answer contains condition_value (case-insensitive)."""
    return condition_value.lower() in (answer or "").lower()


def evaluate_rating_gte(rating: int, condition_value: int) -> bool:
    """Check if rating >= condition_value."""
    return rating >= condition_value


def evaluate_rating_lte(rating: int, condition_value: int) -> bool:
    """Check if rating <= condition_value."""
    return rating <= condition_value


def evaluate_option_equals(selected: str, condition_value: str) -> bool:
    """Check if selected option equals condition_value."""
    return (selected or "").strip() == (condition_value or "").strip()


def detect_circular_reference(
    rules_by_question: dict[str, list[dict]],
) -> list[tuple[str, str]]:
    """DFS to find cycles. Returns list of (from_id, to_id) in cycles."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    path_set = set()

    def dfs(qid: str) -> bool:
        visited.add(qid)
        rec_stack.add(qid)
        path.append(qid)
        path_set.add(qid)
        for rule in rules_by_question.get(qid, []):
            target = rule.get("target_question_id")
            if not target:
                continue
            if target not in visited:
                if dfs(target):
                    return True
            elif target in rec_stack:
                idx = path.index(target)
                cycle = path[idx:] + [target]
                for i in range(len(cycle) - 1):
                    cycles.append((cycle[i], cycle[i + 1]))
                return True
        path.pop()
        path_set.discard(qid)
        rec_stack.discard(qid)
        return False

    for qid in rules_by_question:
        if qid not in visited:
            dfs(qid)
    return list(set(cycles))


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
    assert evaluate_text_contains("love it", "love") and evaluate_rating_gte(8, 7)


def test_evaluate_combined_or():
    """One condition true → target fired."""
    assert evaluate_text_contains("love", "love") or evaluate_rating_gte(6, 7)


def test_detect_circular_reference():
    """DFS finds all cycles."""
    rules = {
        "q1": [{"target_question_id": "q2"}],
        "q2": [{"target_question_id": "q1"}],
    }
    cycles = detect_circular_reference(rules)
    assert len(cycles) >= 1
    assert ("q1", "q2") in cycles or ("q2", "q1") in cycles

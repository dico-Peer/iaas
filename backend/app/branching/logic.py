"""
US-2.03: Branching logic evaluation and circular detection.
Used by interview flow engine and branching endpoint validation.
"""

from typing import Optional


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


def evaluate_single_rule(
    rule: dict,
    answer_text: Optional[str] = None,
    selected_option: Optional[str] = None,
    rating: Optional[int] = None,
) -> bool:
    """Evaluate one branching rule against participant response."""
    ct = rule.get("condition_type")
    cv = rule.get("condition_value")
    if ct == "answer_contains_text":
        return evaluate_text_contains(answer_text or "", str(cv) if cv is not None else "")
    if ct == "selected_option_equals":
        return evaluate_option_equals(selected_option or "", str(cv) if cv is not None else "")
    if ct == "rating_gte":
        try:
            r = int(rating) if rating is not None else 0
            v = int(cv) if cv is not None else 0
            return evaluate_rating_gte(r, v)
        except (TypeError, ValueError):
            return False
    if ct == "rating_lte":
        try:
            r = int(rating) if rating is not None else 0
            v = int(cv) if cv is not None else 0
            return evaluate_rating_lte(r, v)
        except (TypeError, ValueError):
            return False
    return False


def evaluate_rules(
    rules: list,
    answer_text: Optional[str] = None,
    selected_option: Optional[str] = None,
    rating: Optional[int] = None,
) -> Optional[str]:
    """
    Evaluate rules with AND/OR logic. Returns target_question_id of first matching rule,
    or None if no rule matches.
    """
    if not rules:
        return None
    result = evaluate_single_rule(
        rules[0], answer_text=answer_text, selected_option=selected_option, rating=rating
    )
    for i in range(1, len(rules)):
        rule = rules[i]
        op = rule.get("logic_operator", "AND")
        match = evaluate_single_rule(
            rule, answer_text=answer_text, selected_option=selected_option, rating=rating
        )
        if op == "AND":
            result = result and match
        else:
            result = result or match
        if not result and op == "AND":
            return None
    if result and rules:
        return rules[0].get("target_question_id")
    return None


def detect_circular_reference(rules_by_question: dict[str, list[dict]]) -> list[tuple[str, str]]:
    """DFS to find cycles. Returns list of (from_id, to_id) in cycles."""
    cycles: list[tuple[str, str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(qid: str) -> None:
        visited.add(qid)
        rec_stack.add(qid)
        path.append(qid)
        for rule in rules_by_question.get(qid, []):
            target = rule.get("target_question_id")
            if not target:
                continue
            if target not in visited:
                dfs(target)
            elif target in rec_stack:
                idx = path.index(target)
                cycle_path = path[idx:] + [target]
                for i in range(len(cycle_path) - 1):
                    cycles.append((cycle_path[i], cycle_path[i + 1]))
        path.pop()
        rec_stack.discard(qid)

    for qid in rules_by_question:
        if qid not in visited:
            dfs(qid)
    return list(set(cycles))

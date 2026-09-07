"""Presentation policy after junk/score gates: single, list, clarifying, or empty."""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from backend import app_settings
from backend.core.retrieval.match_builder import _fold

# Typed catalog columns used for column-diff chips. Options are never invented.
TYPED_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("micron", "Micron"),
    ("diameter", "Διάμετρος"),
    ("family", "Οικογένεια"),
)
_FIELD_LABELS = {field: label for field, label in TYPED_FIELDS}

PRESENTATION_SINGLE = "single"
PRESENTATION_LIST = "list"
PRESENTATION_CLARIFYING = "clarifying"
PRESENTATION_EMPTY = "empty"

_CODE_KEYS = ("code", "sku_key", "size")


def _norm_token(text: str) -> str:
    return "".join(ch for ch in _fold(text) if ch.isalnum())


def _catalog_of(match: Dict[str, Any]) -> Dict[str, Any]:
    catalog = match.get("catalog")
    return catalog if isinstance(catalog, dict) else {}


def _field_value(match: Dict[str, Any], field: str) -> Optional[str]:
    catalog = _catalog_of(match)
    raw = catalog.get(field)
    if raw is None:
        raw = match.get(field)
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _norm_constraint_value(value: Any) -> str:
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return _fold(text)


def apply_constraints(
    matches: List[Dict[str, Any]],
    constraints: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Keep rows whose typed catalog fields equal the submitted chip answers."""
    if not constraints:
        return list(matches)

    filtered: List[Dict[str, Any]] = []
    for match in matches:
        keep = True
        for item in constraints:
            if not isinstance(item, dict):
                keep = False
                break
            field = str(item.get("field") or "").strip()
            value = item.get("value")
            if not field or value is None or str(value).strip() == "":
                keep = False
                break
            actual = _field_value(match, field)
            if actual is None or _norm_constraint_value(actual) != _norm_constraint_value(value):
                keep = False
                break
        if keep:
            filtered.append(match)
    return filtered


def find_exact_code_match(query: str, matches: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Whole-query or token match against code / sku_key / size (e.g. 6205-2RS)."""
    q = _norm_token(query)
    if len(q) < 4:
        return None
    q_tokens = {_norm_token(tok) for tok in _fold(query).replace("-", " ").split() if _norm_token(tok)}
    for match in matches:
        catalog = _catalog_of(match)
        candidates = [match.get("code"), *(catalog.get(key) for key in _CODE_KEYS)]
        for raw in candidates:
            if raw is None:
                continue
            compact = _norm_token(str(raw))
            if len(compact) < 4:
                continue
            if compact == q or compact in q_tokens:
                return match
    return None


def _score(match: Dict[str, Any]) -> float:
    raw = match.get("score")
    try:
        return float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _gap(matches: Sequence[Dict[str, Any]]) -> float:
    if len(matches) < 2:
        return 1.0
    return _score(matches[0]) - _score(matches[1])


def _leader_ok(matches: Sequence[Dict[str, Any]]) -> bool:
    """Leader survived junk/score gates and has a usable score."""
    if not matches:
        return False
    return _score(matches[0]) >= app_settings.MIN_MATCH_SCORE


def majority_family(matches: Sequence[Dict[str, Any]]) -> Optional[str]:
    families = [_field_value(m, "family") for m in matches]
    present = [fam for fam in families if fam]
    if not present:
        return None
    family, count = Counter(present).most_common(1)[0]
    if count * 2 > len(matches):
        return family
    return None


def restrict_to_family(
    matches: Sequence[Dict[str, Any]],
    family: Optional[str],
) -> List[Dict[str, Any]]:
    if not family:
        return list(matches)
    return [m for m in matches if _field_value(m, "family") == family]


def distinct_typed_values(matches: Sequence[Dict[str, Any]], field: str) -> List[str]:
    """Preserve first-seen order; skip empty / partial ERP values."""
    values: List[str] = []
    seen = set()
    for match in matches:
        value = _field_value(match, field)
        if value is None:
            continue
        key = _norm_constraint_value(value)
        if key in seen:
            continue
        seen.add(key)
        values.append(value)
    return values


def usable_column_diff(
    matches: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """One clarifying question from real typed distinct values among matches."""
    if len(matches) < 2:
        return None

    best: Optional[Tuple[int, int, str, List[str]]] = None
    for priority, (field, _label) in enumerate(TYPED_FIELDS):
        values = distinct_typed_values(matches, field)
        if len(values) < 2:
            continue
        candidate = (-len(values), priority, field, values)
        if best is None or candidate < best:
            best = candidate

    if best is None:
        return None
    _, _, field, values = best
    return {
        "field": field,
        "label": _FIELD_LABELS[field],
        "options": values,
    }


def decide_presentation(
    query: str,
    matches: List[Dict[str, Any]],
    top_k: int = 5,
) -> Dict[str, Any]:
    """Apply the locked presentation policy. `matches` are already gated."""
    list_cap = max(1, min(int(top_k), 5))
    if not matches:
        return {
            "presentation": PRESENTATION_EMPTY,
            "matches": [],
            "clarifying": None,
            "empty": True,
        }

    exact = find_exact_code_match(query, matches)
    if exact is not None:
        return {
            "presentation": PRESENTATION_SINGLE,
            "matches": [exact],
            "clarifying": None,
            "empty": False,
        }

    gap = _gap(matches)
    threshold = app_settings.PRESENTATION_GAP
    if _leader_ok(matches) and gap >= threshold:
        return {
            "presentation": PRESENTATION_SINGLE,
            "matches": [matches[0]],
            "clarifying": None,
            "empty": False,
        }

    top_m = matches[: max(list_cap, app_settings.PRESENTATION_TOP_M)]
    family = majority_family(top_m)
    diff_pool = restrict_to_family(top_m, family)
    if not diff_pool:
        diff_pool = list(top_m)

    clarifying = usable_column_diff(diff_pool) if gap < threshold else None
    if clarifying:
        shown = diff_pool[:list_cap]
        return {
            "presentation": PRESENTATION_CLARIFYING,
            "matches": shown,
            "clarifying": clarifying,
            "empty": False,
        }

    return {
        "presentation": PRESENTATION_LIST,
        "matches": matches[:list_cap],
        "clarifying": None,
        "empty": False,
    }


def normalize_constraints(raw: Optional[Iterable[Any]]) -> List[Dict[str, str]]:
    if not raw:
        return []
    out: List[Dict[str, str]] = []
    for item in raw:
        if hasattr(item, "field") and hasattr(item, "value"):
            field, value = item.field, item.value
        elif isinstance(item, dict):
            field, value = item.get("field"), item.get("value")
        else:
            continue
        if field is None or value is None:
            continue
        field_s, value_s = str(field).strip(), str(value).strip()
        if field_s and value_s:
            out.append({"field": field_s, "value": value_s})
    return out

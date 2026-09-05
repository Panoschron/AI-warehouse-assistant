"""Map retrieved catalog rows onto the locked /query match contract."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend import app_settings

# Column aliases seen in SoftOne-like exports (EN + EL).
_CODE_KEYS = (
    "code",
    "κωδικός",
    "κωδικος",
    "item_code",
    "itemcode",
    "sku",
    "id",
)
_DESC_KEYS = (
    "description",
    "περιγραφή",
    "περιγραφη",
    "name",
    "όνομα",
    "ονομα",
    "desc",
)
_LOCATION_KEYS = (
    "location",
    "shelf",
    "ράφι",
    "ραφι",
    "θέση",
    "θεση",
    "bin",
    "aisle",
    "warehouse_location",
)


def _norm_key(key: str) -> str:
    return " ".join(str(key).strip().lower().replace("\n", " ").split())


def _lookup(fields: Dict[str, Any], aliases: Iterable[str]) -> Optional[str]:
    normalized = {_norm_key(k): v for k, v in fields.items()}
    for alias in aliases:
        value = normalized.get(_norm_key(alias))
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return None


def catalog_fields(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap {id, metadata: {...}} or a flat row into a single field dict."""
    if not entry:
        return {}
    nested = entry.get("metadata")
    if isinstance(nested, dict):
        fields = dict(nested)
        if entry.get("id") and "id" not in fields:
            fields["id"] = entry["id"]
        return fields
    return dict(entry)


def resolve_code(fields: Dict[str, Any], fallback: str = "") -> str:
    return _lookup(fields, _CODE_KEYS) or fallback or ""


def resolve_description(fields: Dict[str, Any]) -> str:
    return _lookup(fields, _DESC_KEYS) or ""


def resolve_location(fields: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """Return (location, location_state). Never invent a shelf."""
    location = _lookup(fields, _LOCATION_KEYS)
    if location:
        return location, "present"
    return None, "empty"


def _score_from_result(result: Dict[str, Any]) -> Optional[float]:
    """IndexFlatIP + normalized embeddings: FAISS 'distance' is cosine similarity."""
    raw = result.get("score", result.get("distance"))
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def build_matches(
    results: List[Dict[str, Any]],
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Turn formatter rows into contract matches (explain is filled later)."""
    threshold = app_settings.MIN_MATCH_SCORE if min_score is None else min_score
    matches: List[Dict[str, Any]] = []

    for result in results:
        entry = result.get("metadata") if isinstance(result.get("metadata"), dict) else result
        fields = catalog_fields(entry or {})
        score = _score_from_result(result)
        if score is not None and score < threshold:
            continue

        code = resolve_code(fields, fallback=str(entry.get("id") or "") if entry else "")
        description = resolve_description(fields)
        location, location_state = resolve_location(fields)

        match: Dict[str, Any] = {
            "code": code,
            "description": description,
            "location": location,
            "location_state": location_state,
            "catalog": fields,
        }
        if score is not None:
            match["score"] = round(score, 4)
        matches.append(match)

    return matches

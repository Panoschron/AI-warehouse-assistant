"""Grounded per-match explanations. Never invent catalog specs."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.clients.base_llm_client import BaseLLMClient
from backend.core.generation.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

MISSING = "δεν υπάρχει στο κατάλογο"

# Extra catalog keys we may surface when present (never invented).
_OPTIONAL_LABELS = (
    ("category", "Κατηγορία"),
    ("κατηγορία", "Κατηγορία"),
    ("manufacturer", "Κατασκευαστής"),
    ("κατασκευαστής", "Κατασκευαστής"),
    ("size", "Διάσταση"),
    ("pressure", "Πίεση"),
    ("unit", "Μονάδα"),
    ("stock", "Απόθεμα"),
    ("απόθεμα", "Απόθεμα"),
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_user_query(query: str, max_len: int = 500) -> str:
    """Strip control chars / fences and cap length before the query enters a prompt."""
    if not query:
        return ""
    cleaned = _CONTROL_CHARS.sub("", str(query))
    cleaned = cleaned.replace("```", "'''").replace("</", "< /")
    return cleaned.strip()[:max_len]


def wrap_untrusted_query(query: str) -> str:
    safe = sanitize_user_query(query)
    return f"<user_query>\n{safe}\n</user_query>"


def _field(catalog: Dict[str, Any], *keys: str) -> Optional[str]:
    lowered = {str(k).strip().lower(): v for k, v in catalog.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return None


def template_explain(match: Dict[str, Any]) -> str:
    """Deterministic explain from catalog fields only — works offline, no LLM."""
    catalog = match.get("catalog") or {}
    code = match.get("code") or _field(catalog, "code", "κωδικός") or MISSING
    description = match.get("description") or _field(catalog, "description", "περιγραφή") or MISSING

    if match.get("location_state") == "present" and match.get("location"):
        location_txt = match["location"]
    else:
        location_txt = MISSING

    parts = [
        f"Κωδικός {code} στον κατάλογο: {description}.",
        f"Θέση/ράφι: {location_txt}.",
    ]

    seen_labels = set()
    for key, label in _OPTIONAL_LABELS:
        if label in seen_labels:
            continue
        value = _field(catalog, key)
        if value:
            parts.append(f"{label}: {value}.")
            seen_labels.add(label)

    return " ".join(parts)


def _parse_explain_list(raw: str, expected: int) -> Optional[List[str]]:
    if not raw:
        return None
    text = raw.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(parsed, list) or len(parsed) != expected:
        return None
    explains: List[str] = []
    for item in parsed:
        if not isinstance(item, str) or not item.strip():
            return None
        explains.append(item.strip())
    return explains


def attach_explains(
    query: str,
    matches: List[Dict[str, Any]],
    prompt_builder: Optional[PromptBuilder] = None,
    llm_client: Optional[BaseLLMClient] = None,
) -> List[Dict[str, Any]]:
    """Add required per-match `explain`. LLM is optional; template is the fallback."""
    templates = [template_explain(match) for match in matches]
    explains = templates

    if matches and llm_client and prompt_builder:
        try:
            prompt = prompt_builder.build_match_explain_prompt(query, matches)
            raw = llm_client.generate(
                prompt=prompt,
                system_prompt=prompt_builder.explain_system_prompt,
            )
            parsed = _parse_explain_list(raw, expected=len(matches))
            if parsed:
                explains = parsed
            else:
                logger.warning("LLM explain payload was not usable; using template explains")
        except Exception:
            logger.exception("LLM explain failed; using template explains")

    annotated: List[Dict[str, Any]] = []
    for match, explain in zip(matches, explains):
        item = {k: v for k, v in match.items() if k != "catalog"}
        item["explain"] = explain
        annotated.append(item)
    return annotated


def template_nl_response(matches: List[Dict[str, Any]]) -> str:
    if not matches:
        return "Δεν βρέθηκαν σχετικά είδη στον κατάλογο."
    top = matches[0]
    loc = top.get("location") if top.get("location_state") == "present" else MISSING
    return (
        f"Βρέθηκαν {len(matches)} αποτελέσματα. "
        f"Κορυφαίο: {top.get('code', '')} — {top.get('description', '')} "
        f"(θέση: {loc})."
    )

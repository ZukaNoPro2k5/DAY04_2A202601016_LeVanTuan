from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
}


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def _normalize_url(url: str) -> str:
    if not url.strip():
        return ""

    parts = urlsplit(url.strip())
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMS
    ]

    path = parts.path.rstrip("/") or "/"

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(sorted(filtered_query)),
            "",
        )
    )


def deduplicate_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    source_items = items or []
    unique_items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in source_items:
        if not isinstance(item, dict):
            continue

        normalized_url = _normalize_url(str(item.get("url") or ""))
        normalized_title = _normalize_title(str(item.get("title") or ""))

        if normalized_url:
            identity = f"url:{normalized_url}"
        elif normalized_title:
            identity = f"title:{normalized_title}"
        else:
            identity = f"position:{len(unique_items)}"

        if identity in seen:
            continue

        seen.add(identity)
        unique_items.append(item)

    return {
        "tool": "deduplicate",
        "input_count": len(source_items),
        "removed_count": len(source_items) - len(unique_items),
        "items": unique_items,
    }
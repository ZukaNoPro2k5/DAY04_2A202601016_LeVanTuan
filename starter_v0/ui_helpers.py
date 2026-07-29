from __future__ import annotations

import csv
import json
import os
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


SECRET_ENV_NAMES = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "TAVILY_API_KEY",
    "FIRECRAWL_API_KEY",
    "RAPIDAPI_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)

SENSITIVE_KEY_PARTS = ("api_key", "apikey", "token", "password", "secret", "authorization")
TELEGRAM_BOT_URL_RE = re.compile(r"https://api\.telegram\.org/bot[^/\s]+", re.IGNORECASE)
VERSION_RE = re.compile(r"^v(\d+)$", re.IGNORECASE)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "session"


def version_sort_key(version: str) -> tuple[int, str]:
    match = VERSION_RE.match(version.strip())
    if match:
        return int(match.group(1)), version
    return -1, version


def latest_version_label(version_log_path: Path) -> str:
    if not version_log_path.exists():
        return "v0"
    with version_log_path.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("version")]
    if not rows:
        return "v0"
    return max((row["version"].strip() for row in rows), key=version_sort_key)


def build_chat_messages(
    *,
    system_prompt: str,
    history: list[dict[str, str]],
    user_text: str,
    history_window: int = 5,
) -> list[dict[str, str]]:
    if history_window <= 0:
        trimmed: list[dict[str, str]] = []
    else:
        trimmed = history[-history_window * 2 :]
    return [
        {"role": "system", "content": system_prompt},
        *trimmed,
        {"role": "user", "content": user_text},
    ]


def secret_availability() -> dict[str, bool]:
    return {name: bool(os.getenv(name)) for name in SECRET_ENV_NAMES}


def _secret_replacements() -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    for name in SECRET_ENV_NAMES:
        value = os.getenv(name)
        if value and len(value) >= 4:
            replacements.append((value, f"[REDACTED:{name}]"))
    return sorted(replacements, key=lambda item: len(item[0]), reverse=True)


def redact_text(value: str) -> str:
    redacted = TELEGRAM_BOT_URL_RE.sub("https://api.telegram.org/bot[REDACTED]", value)
    for secret, replacement in _secret_replacements():
        redacted = redacted.replace(secret, replacement)
    return redacted


def sanitize_payload(value: Any, *, parent_key: str = "") -> Any:
    normalized_key = parent_key.lower().replace("-", "_")
    if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
        return "[REDACTED]" if value not in (None, "", False) else value
    if isinstance(value, dict):
        return {
            key: sanitize_payload(item, parent_key=str(key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_payload(item, parent_key=parent_key) for item in value]
    if isinstance(value, tuple):
        return [sanitize_payload(item, parent_key=parent_key) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def json_text(value: Any, *, max_chars: int = 8000) -> str:
    rendered = json.dumps(sanitize_payload(value), ensure_ascii=False, indent=2, default=str)
    if len(rendered) <= max_chars:
        return rendered
    omitted = len(rendered) - max_chars
    return f"{rendered[:max_chars]}\n... <truncated {omitted} characters>"


def create_transcript(
    *,
    transcripts_dir: Path,
    artifact: dict[str, str],
    provider: str,
    model: str,
    system_prompt_path: Path,
    tools_path: Path,
    history_window: int,
    max_tool_rounds: int,
) -> tuple[dict[str, Any], Path]:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = safe_slug(f"ui_{artifact['version']}_{provider}_{timestamp}")
    transcript_path = transcripts_dir / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact,
        "provider": provider,
        "model": model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "source": "streamlit",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    write_transcript(transcript_path, transcript)
    return transcript, transcript_path


def append_transcript_turn(
    transcript: dict[str, Any],
    transcript_path: Path,
    turn: dict[str, Any],
) -> None:
    transcript["turns"].append(sanitize_payload(deepcopy(turn)))
    write_transcript(transcript_path, transcript)


def write_transcript(path: Path, transcript: dict[str, Any]) -> None:
    safe_transcript = sanitize_payload(deepcopy(transcript))
    safe_transcript["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(safe_transcript, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def load_latest_base_runs(runs_dir: Path) -> list[dict[str, Any]]:
    latest_by_version: dict[str, tuple[float, dict[str, Any]]] = {}
    if not runs_dir.exists():
        return []

    for path in runs_dir.glob("v*_B_base_*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("suite") != "base":
            continue
        version = str(payload.get("version") or "")
        if not VERSION_RE.match(version):
            continue
        candidate = (path.stat().st_mtime, {**payload, "_path": str(path)})
        current = latest_by_version.get(version)
        if current is None or candidate[0] > current[0]:
            latest_by_version[version] = candidate

    return [
        latest_by_version[version][1]
        for version in sorted(latest_by_version, key=version_sort_key)
    ]


def evidence_metrics(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        summary = run.get("summary", {})
        rows.append(
            {
                "Version": run.get("version"),
                "Accuracy": summary.get("case_accuracy"),
                "Routing": summary.get("tool_routing_accuracy"),
                "Arguments": summary.get("argument_accuracy"),
                "Multi-turn": summary.get("multiturn_accuracy"),
                "Provider errors": summary.get("provider_error_cases"),
                "Artifact": run.get("artifact_version"),
            }
        )
    return rows


def evidence_case_ids(runs: list[dict[str, Any]]) -> list[str]:
    case_ids = {
        result.get("id")
        for run in runs
        for result in run.get("results", [])
        if result.get("id")
    }
    return sorted(case_ids)


def evidence_case_rows(runs: list[dict[str, Any]], case_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        result = next(
            (item for item in run.get("results", []) if item.get("id") == case_id),
            None,
        )
        if result is None:
            continue
        evaluation = result.get("result", {})
        calls = evaluation.get("actual_tool_calls") or []
        rows.append(
            {
                "version": run.get("version"),
                "artifact_version": run.get("artifact_version"),
                "passed": bool(evaluation.get("passed")),
                "input": sanitize_payload(result.get("input")),
                "expected": sanitize_payload(result.get("expect")),
                "actual_tool_calls": sanitize_payload(calls),
                "failures": sanitize_payload(evaluation.get("failures") or []),
                "run_file": run.get("_path"),
            }
        )
    return rows

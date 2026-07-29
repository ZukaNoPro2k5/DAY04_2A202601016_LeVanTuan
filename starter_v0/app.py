from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from ui_helpers import (
    append_transcript_turn,
    build_chat_messages,
    create_transcript,
    evidence_case_ids,
    evidence_case_rows,
    evidence_metrics,
    json_text,
    latest_version_label,
    load_latest_base_runs,
    now_iso,
    sanitize_payload,
    secret_availability,
)
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
VERSION_LOG_PATH = ARTIFACTS_DIR / "version_log.csv"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"

PROVIDER_NAME = "openrouter"
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

DEMO_PROMPTS = (
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tóm tắt 5 tweet mới nhất giúp mình.",
    "Đăng bản tin này lên Telegram giúp mình.",
)


st.set_page_config(
    page_title="Research Agent Console",
    page_icon="⌁",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_lab_env(ROOT)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
          --rac-bg: oklch(1 0 0);
          --rac-surface: oklch(0.968 0.008 180);
          --rac-surface-strong: oklch(0.935 0.014 180);
          --rac-ink: oklch(0.205 0.018 180);
          --rac-muted: oklch(0.44 0.025 180);
          --rac-border: oklch(0.84 0.018 180);
          --rac-primary: oklch(0.50 0.10 180);
          --rac-primary-deep: oklch(0.42 0.095 180);
          --rac-accent: oklch(0.30 0.11 280);
          --rac-success: oklch(0.48 0.12 145);
          --rac-warning: oklch(0.62 0.13 75);
          --rac-error: oklch(0.49 0.17 25);
          --rac-focus: oklch(0.58 0.13 180);
          --rac-radius-sm: 6px;
          --rac-radius-md: 12px;
          --rac-ease: cubic-bezier(0.22, 1, 0.36, 1);
        }

        html, body, [class*="css"] {
          font-size: 16px;
        }

        .stApp {
          background: var(--rac-bg);
          color: var(--rac-ink);
        }

        [data-testid="stAppViewContainer"] > .main .block-container {
          max-width: 1560px;
          padding-top: 1.4rem;
          padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
          background: var(--rac-surface);
          border-right: 1px solid var(--rac-border);
        }

        [data-testid="stSidebar"] hr {
          border-color: var(--rac-border);
        }

        .rac-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 1.5rem;
          margin: 0 0 1.1rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid var(--rac-border);
        }

        .rac-header h1 {
          margin: 0;
          color: var(--rac-ink);
          font-size: 1.75rem;
          line-height: 1.15;
          letter-spacing: -0.025em;
          text-wrap: balance;
        }

        .rac-header p {
          margin: 0.42rem 0 0;
          max-width: 68ch;
          color: var(--rac-muted);
          line-height: 1.5;
        }

        .rac-badges {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 0.45rem;
        }

        .rac-badge {
          display: inline-flex;
          align-items: center;
          min-height: 30px;
          padding: 0.25rem 0.62rem;
          border: 1px solid var(--rac-border);
          border-radius: 999px;
          background: var(--rac-bg);
          color: var(--rac-ink);
          font-size: 0.82rem;
          font-weight: 650;
          white-space: nowrap;
        }

        .rac-badge--ready {
          border-color: var(--rac-primary);
          color: var(--rac-primary-deep);
        }

        .rac-badge--error {
          border-color: var(--rac-error);
          color: var(--rac-error);
        }

        .rac-empty {
          padding: 1.1rem 0 0.5rem;
          color: var(--rac-muted);
          max-width: 64ch;
        }

        .rac-empty strong {
          color: var(--rac-ink);
        }

        .rac-trace-summary {
          padding: 0.72rem 0.8rem;
          margin-bottom: 0.65rem;
          border: 1px solid var(--rac-border);
          border-radius: var(--rac-radius-sm);
          background: var(--rac-surface);
          color: var(--rac-ink);
          line-height: 1.45;
        }

        .rac-state {
          display: inline-flex;
          align-items: center;
          gap: 0.38rem;
          font-weight: 700;
        }

        .rac-state::before {
          content: "";
          width: 0.55rem;
          height: 0.55rem;
          border-radius: 50%;
          background: var(--rac-muted);
        }

        .rac-state--success::before { background: var(--rac-success); }
        .rac-state--waiting::before { background: var(--rac-warning); }
        .rac-state--error::before { background: var(--rac-error); }

        [data-testid="stChatMessage"] {
          background: transparent;
          border-bottom: 1px solid var(--rac-border);
          border-radius: 0;
          padding-block: 0.8rem;
        }

        [data-testid="stChatMessage"]:last-child {
          border-bottom: none;
        }

        [data-testid="stExpander"] {
          border-color: var(--rac-border);
          border-radius: var(--rac-radius-sm);
          background: var(--rac-bg);
        }

        [data-testid="stCode"] code {
          font-size: 0.84rem;
          line-height: 1.5;
        }

        .stButton > button,
        .stDownloadButton > button {
          min-height: 40px;
          border-radius: var(--rac-radius-sm);
          border: 1px solid var(--rac-border);
          font-weight: 650;
          transition:
            border-color 180ms var(--rac-ease),
            background 180ms var(--rac-ease),
            color 180ms var(--rac-ease);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
          border-color: var(--rac-primary);
          color: var(--rac-primary-deep);
        }

        button:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        [role="button"]:focus-visible {
          outline: 3px solid var(--rac-focus) !important;
          outline-offset: 2px !important;
        }

        [data-testid="stChatInput"] {
          border-color: var(--rac-border);
          border-radius: var(--rac-radius-md);
        }

        .rac-evidence-pass {
          color: var(--rac-success);
          font-weight: 750;
        }

        .rac-evidence-fail {
          color: var(--rac-error);
          font-weight: 750;
        }

        .rac-mono {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
          font-size: 0.82rem;
          overflow-wrap: anywhere;
        }

        @media (max-width: 760px) {
          [data-testid="stAppViewContainer"] > .main .block-container {
            padding-inline: 1rem;
          }

          .rac-header {
            flex-direction: column;
          }

          .rac-badges {
            justify-content: flex-start;
          }

          [data-testid="stHorizontalBlock"] {
            flex-direction: column;
          }

          [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 auto !important;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    defaults: dict[str, Any] = {
        "history": [],
        "turns": [],
        "transcript": None,
        "transcript_path": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session() -> None:
    for key in ("history", "turns", "transcript", "transcript_path"):
        st.session_state.pop(key, None)
    initialize_state()


def status_meta(status: str) -> tuple[str, str]:
    mapping = {
        "answered": ("Hoàn tất", "success"),
        "waiting_for_user": ("Đang chờ bạn", "waiting"),
        "max_tool_rounds": ("Đã dừng ở giới hạn round", "error"),
        "provider_error": ("Provider error", "error"),
    }
    return mapping.get(status, (status.replace("_", " ").title(), "waiting"))


def render_header(*, artifact_version: str, model: str, ready: bool) -> None:
    ready_class = "rac-badge--ready" if ready else "rac-badge--error"
    ready_text = "API ready" if ready else "API unavailable"
    st.markdown(
        f"""
        <div class="rac-header">
          <div>
            <h1>Research Agent Console</h1>
            <p>Live research, observable tool calls, and version evidence in one classroom-ready view.</p>
          </div>
          <div class="rac-badges" aria-label="Runtime metadata">
            <span class="rac-badge">{html.escape(PROVIDER_NAME)}</span>
            <span class="rac-badge">{html.escape(model)}</span>
            <span class="rac-badge">{html.escape(artifact_version)}</span>
            <span class="rac-badge {ready_class}">{ready_text}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(
    *,
    version: str,
    artifact_version: str,
    model: str,
    availability: dict[str, bool],
) -> None:
    with st.sidebar:
        st.subheader("Runtime")
        st.text_input("Provider", PROVIDER_NAME, disabled=True)
        st.text_input("Model", model, disabled=True)
        st.text_input("Live artifact", version, disabled=True)
        st.caption(artifact_version)

        st.divider()
        st.subheader("API readiness")
        readiness = {
            "OpenRouter": availability.get("OPENROUTER_API_KEY", False),
            "Tavily · lookup": availability.get("TAVILY_API_KEY", False),
            "Firecrawl · fetch": availability.get("FIRECRAWL_API_KEY", False),
            "RapidAPI · social": availability.get("RAPIDAPI_KEY", False),
        }
        for label, ready in readiness.items():
            st.write(f"{'●' if ready else '○'} {label} — {'ready' if ready else 'missing'}")

        telegram_ready = availability.get("TELEGRAM_BOT_TOKEN", False) and availability.get(
            "TELEGRAM_CHAT_ID", False
        )
        if telegram_ready:
            st.warning("Telegram live-send credentials are set. Keep demo requests at the confirmation boundary.")
        else:
            st.caption("Telegram live send disabled — safe demo mode.")

        st.divider()
        st.subheader("Conversation")
        st.write(f"History window: **{HISTORY_WINDOW}** pairs")
        st.write(f"Max tool rounds: **{MAX_TOOL_ROUNDS}**")
        if st.button("Start a new session", width="stretch"):
            reset_session()
            st.rerun()

        transcript = st.session_state.get("transcript")
        transcript_path = st.session_state.get("transcript_path")
        if transcript and transcript_path:
            st.caption("Transcript")
            st.code(transcript.get("transcript_id", ""), language=None)
            st.download_button(
                "Download transcript",
                data=json.dumps(sanitize_payload(transcript), ensure_ascii=False, indent=2),
                file_name=Path(transcript_path).name,
                mime="application/json",
                width="stretch",
            )


def render_chat_history() -> None:
    if not st.session_state.history:
        st.markdown(
            """
            <div class="rac-empty">
              <strong>Start with a rehearsed scenario.</strong><br>
              The response will stay on the left while every tool round appears in the trace panel.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def tool_result_label(event: dict[str, Any]) -> str:
    result = event.get("result")
    if isinstance(result, dict):
        if result.get("error"):
            return "error"
        if result.get("awaiting_user") or result.get("status") == "needs_confirmation":
            return "waiting"
    return "success"


def render_tool_event(event: dict[str, Any]) -> None:
    tool_name = str(event.get("tool") or "unknown")
    state = tool_result_label(event)
    state_label = {"success": "success", "waiting": "waiting", "error": "error"}[state]
    st.markdown(f"**{tool_name}** · {state_label}")
    st.caption("Arguments")
    st.code(json_text(event.get("args") or {}), language="json")

    result = event.get("result")
    if isinstance(result, dict):
        summary_bits: list[str] = []
        if isinstance(result.get("items"), list):
            summary_bits.append(f"{len(result['items'])} item(s)")
        if result.get("item_count") is not None:
            summary_bits.append(f"item_count={result['item_count']}")
        if result.get("removed_count") is not None:
            summary_bits.append(f"removed={result['removed_count']}")
        if result.get("status"):
            summary_bits.append(f"status={result['status']}")
        if result.get("error"):
            summary_bits.append(f"error={result['error']}")
        if summary_bits:
            st.caption(" · ".join(summary_bits))
    st.caption("Result")
    st.code(json_text(result), language="json")


def render_trace(turn: dict[str, Any] | None) -> None:
    st.subheader("Tool trace")
    if turn is None:
        st.markdown(
            """
            <div class="rac-empty">
              <strong>No trace yet.</strong><br>
              Submit a prompt to inspect rounds, arguments, results, and errors here.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    status = str(turn.get("status") or "unknown")
    status_label, status_class = status_meta(status)
    event_count = len(turn.get("tool_events") or [])
    st.markdown(
        f"""
        <div class="rac-trace-summary">
          <span class="rac-state rac-state--{status_class}">{html.escape(status_label)}</span><br>
          Turn {turn.get("turn_index", "?")} · {event_count} tool event(s)
        </div>
        """,
        unsafe_allow_html=True,
    )

    rounds = turn.get("rounds") or []
    if not rounds:
        if turn.get("error"):
            st.error(str(turn["error"]))
        else:
            st.info("This turn produced no recorded rounds.")
        return

    for round_record in rounds:
        round_index = round_record.get("round", "?")
        calls = round_record.get("tool_calls") or []
        call_names = ", ".join(str(call.get("name")) for call in calls) if calls else "no tool"
        with st.expander(f"Round {round_index} · {call_names}", expanded=True):
            if round_record.get("assistant_text"):
                st.caption("Assistant planning text")
                st.write(round_record["assistant_text"])
            if not calls:
                st.caption("Model answered directly without a tool call.")
            results = round_record.get("tool_results") or []
            for result_index, event in enumerate(results):
                if result_index:
                    st.divider()
                render_tool_event(event)

    transcript = st.session_state.get("transcript")
    if transcript:
        st.caption(f"Transcript: {transcript.get('transcript_id')}")


def ensure_transcript(
    *,
    artifact: dict[str, str],
    model: str,
) -> tuple[dict[str, Any], Path]:
    if st.session_state.transcript is None or st.session_state.transcript_path is None:
        transcript, transcript_path = create_transcript(
            transcripts_dir=TRANSCRIPTS_DIR,
            artifact=artifact,
            provider=PROVIDER_NAME,
            model=model,
            system_prompt_path=SYSTEM_PROMPT_PATH,
            tools_path=TOOLS_PATH,
            history_window=HISTORY_WINDOW,
            max_tool_rounds=MAX_TOOL_ROUNDS,
        )
        st.session_state.transcript = transcript
        st.session_state.transcript_path = transcript_path
    return st.session_state.transcript, Path(st.session_state.transcript_path)


def process_prompt(
    *,
    user_text: str,
    provider: Any,
    model: str,
    system_prompt: str,
    openai_tools: list[dict[str, Any]],
    artifact: dict[str, str],
) -> None:
    transcript, transcript_path = ensure_transcript(artifact=artifact, model=model)
    turn_index = len(st.session_state.turns) + 1
    turn: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = build_chat_messages(
        system_prompt=system_prompt,
        history=st.session_state.history,
        user_text=user_text,
        history_window=HISTORY_WINDOW,
    )

    with st.status("Routing request and executing tools…", expanded=True) as status_box:
        st.write("Using the current prompt and tool declarations.")
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            safe_result = sanitize_payload(result)
            turn.update(safe_result)
            assistant_text = str(safe_result.get("assistant_text") or "")
            result_status = str(safe_result.get("status") or "answered")
            if result_status == "waiting_for_user":
                status_box.update(
                    label="The agent needs one more detail",
                    state="complete",
                    expanded=False,
                )
            elif result_status == "max_tool_rounds":
                status_box.update(
                    label="Stopped at the tool-round limit",
                    state="error",
                    expanded=True,
                )
            else:
                status_box.update(label="Response complete", state="complete", expanded=False)
        except Exception as exc:
            assistant_text = "The provider could not complete this request. Inspect the trace and try again."
            turn.update(
                {
                    "status": "provider_error",
                    "assistant_text": assistant_text,
                    "error": sanitize_payload(f"{type(exc).__name__}: {exc}"),
                }
            )
            status_box.update(label="Provider error", state="error", expanded=True)
            st.error(turn["error"])

    turn["ended_at"] = now_iso()
    safe_turn = sanitize_payload(turn)
    st.session_state.turns.append(safe_turn)
    st.session_state.history.append({"role": "user", "content": user_text})
    st.session_state.history.append({"role": "assistant", "content": assistant_text})
    append_transcript_turn(transcript, transcript_path, safe_turn)


def render_live_tab(
    *,
    provider: Any,
    model: str,
    provider_ready: bool,
    system_prompt: str,
    openai_tools: list[dict[str, Any]],
    artifact: dict[str, str],
) -> None:
    chat_column, trace_column = st.columns([3, 2], gap="large")
    selected_prompt: str | None = None

    with chat_column:
        st.subheader("Conversation")
        conversation_height = 120 if not st.session_state.history else 235
        conversation = st.container(height=conversation_height)
        with conversation:
            render_chat_history()

        if not st.session_state.history:
            st.caption("Rehearsed prompts")
            prompt_columns = st.columns(3, gap="small")
            for index, example in enumerate(DEMO_PROMPTS):
                with prompt_columns[index]:
                    if st.button(example, key=f"demo_prompt_{index}", width="stretch"):
                        selected_prompt = example

        if provider_ready:
            typed_prompt = st.chat_input("Ask for research, provide a URL, or test a safety boundary…")
        else:
            typed_prompt = None
            st.error("Configure OPENROUTER_API_KEY in .env before using live chat.")

    with trace_column:
        selected_turn: dict[str, Any] | None = None
        if st.session_state.turns:
            turn_options = list(range(len(st.session_state.turns)))
            selected_index = st.selectbox(
                "Inspect turn",
                options=turn_options,
                index=len(turn_options) - 1,
                format_func=lambda value: (
                    f"Turn {value + 1} · "
                    f"{status_meta(str(st.session_state.turns[value].get('status')))[0]}"
                ),
                key=f"trace_turn_select_{len(turn_options)}",
            )
            selected_turn = st.session_state.turns[selected_index]
        trace_panel = st.container(height=195)
        with trace_panel:
            render_trace(selected_turn)

    prompt = selected_prompt or typed_prompt
    if prompt:
        process_prompt(
            user_text=prompt.strip(),
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            openai_tools=openai_tools,
            artifact=artifact,
        )
        st.rerun()


def render_evidence_tab() -> None:
    runs = load_latest_base_runs(RUNS_DIR)
    if not runs:
        st.info("No base run JSON files are available yet.")
        return

    st.subheader("Version evidence")
    st.write(
        "Stored runs make the same fixed scenario comparable across artifact versions. "
        "Live chat always uses only the current prompt and tool declarations."
    )
    st.dataframe(evidence_metrics(runs), hide_index=True, width="stretch")

    case_ids = evidence_case_ids(runs)
    default_index = case_ids.index("R10_missing_handle") if "R10_missing_handle" in case_ids else 0
    case_id = st.selectbox("Compare one fixed base case", case_ids, index=default_index)
    rows = evidence_case_rows(runs, case_id)

    if rows and rows[0].get("input") is not None:
        st.caption("Scenario")
        input_value = rows[0]["input"]
        if isinstance(input_value, str):
            st.info(input_value)
        else:
            st.json(input_value, expanded=False)

    for row in rows:
        pass_class = "rac-evidence-pass" if row["passed"] else "rac-evidence-fail"
        pass_label = "PASS" if row["passed"] else "FAIL"
        with st.expander(
            f"{row['version']} · {pass_label} · {row['artifact_version']}",
            expanded=not row["passed"],
        ):
            st.markdown(
                f'<span class="{pass_class}">{pass_label}</span>',
                unsafe_allow_html=True,
            )
            st.caption("Expected behavior")
            st.code(json_text(row["expected"]), language="json")
            st.caption("Actual tool calls")
            st.code(json_text(row["actual_tool_calls"]), language="json")
            if row["failures"]:
                st.caption("Failures")
                st.code(json_text(row["failures"]), language="json")
            else:
                st.caption("No grader mismatches.")
            st.markdown(
                f'<div class="rac-mono">{html.escape(str(row["run_file"]))}</div>',
                unsafe_allow_html=True,
            )


inject_styles()
initialize_state()

system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(TOOLS_PATH)
openai_tools = to_openai_tools(tool_declarations)
current_version = latest_version_label(VERSION_LOG_PATH)
artifact_object = build_artifact_version(current_version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
artifact = artifact_version_dict(artifact_object)
provider = make_provider(PROVIDER_NAME)
model = str(getattr(provider, "default_model", "openai/gpt-4o-mini"))
availability = secret_availability()
provider_ready = availability.get("OPENROUTER_API_KEY", False)

render_sidebar(
    version=current_version,
    artifact_version=artifact["artifact_version"],
    model=model,
    availability=availability,
)
render_header(
    artifact_version=artifact["artifact_version"],
    model=model,
    ready=provider_ready,
)

live_tab, evidence_tab = st.tabs(["Live Agent", "Version Evidence"])
with live_tab:
    render_live_tab(
        provider=provider,
        model=model,
        provider_ready=provider_ready,
        system_prompt=system_prompt,
        openai_tools=openai_tools,
        artifact=artifact,
    )
with evidence_tab:
    render_evidence_tab()

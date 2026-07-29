# Day 04 Lab — working rules and submission checklist

## Ownership

- This is a **group/team lab** (the brief consistently says "nhóm" / "team").
- Implementation owner for this workspace: **Lê Văn Tuấn — MSSV 2A202601016**.
- Although the lab is group-based, Tuấn will complete the implementation solo unless
  instructed otherwise. Keep the report's Team/Members fields truthful before submission.

## Required deliverables (core)

- A real-provider research agent; provider preflight must pass.
- At least **5 declared tools** in `starter_v0/artifacts/tools.yaml`.
- Run the fixed base evaluation as **v0**.
- Make and evaluate **three genuine, evidence-driven optimization iterations**:
  `v1`, `v2`, and `v3`. Do not submit three identical reruns.
- Update `starter_v0/artifacts/version_log.csv` after every version, including at
  least v0–v3, with hashes, rationale/hypothesis, before/after metric, and run path.
- Add at least **one team-authored tool** (built-in optional tools do not count):
  implementation, `TOOL.md`, registry entry in `tools/__init__.py`, YAML declaration,
  and a direct smoke test with real implementation output.
- Create **exactly 10** cases in `starter_v0/data/eval_group.json`:
  **5 single-turn** using `query`, and **5 multi-turn** using `turns`. Each case must
  have `id`, `phase: "B"`, an allowed `failure_type`, an `expect` of `tool_calls` or
  `no_tool`, and `metadata.what_it_tests`. The final turn of each multi-turn case must
  be the user turn being graded.
- Run the group suite at v3.
- Run live chat and retain transcripts. Evidence must cover a normal research request,
  missing information followed by a user reply, and a sensitive action/confirmation
  boundary.
- Build a functioning UI (Streamlit recommended, any equivalent framework allowed).
  It must show request/response, tool trace (name, args, round/status, result/error),
  transcript/run/artifact version. For Streamlit, reuse `run_model_tool_loop` in
  `chat.py`, write `app.py`, add Streamlit to `requirements.txt`, and pass at
  `http://localhost:8501`.
- Complete `starter_v0/artifacts/REPORT.md` using actual logs.
  - Part A (agent overview, tools, example prompts, rehearsed demo) is due **before
    11:30** for the demo.
  - Part B (v0–v3 evidence, failure analysis, group eval, live-chat evidence, tool
    evidence, reflection) is completed afterward for submission.

## Evidence validity rules

- A reported suite is valid only when `provider_error_cases == 0` and
  `measured_cases == total_cases`.
- Manually review every `tool_results` error even if routing accuracy says PASS.
- Inspect run JSON (`failures`, `observed_mismatch`, actual calls/results) before each
  hypothesis. Keep actual `runs/*.json`, transcript JSON, and relevant CSV analysis.
- In each prompt/tool-routing experiment, change only `artifacts/system_prompt.md`
  and/or `artifacts/tools.yaml`; do not alter fixed base queries, expected args, or
  behavior. Renaming a tool is the sole exception: synchronize its tool-name field.
- If a tool is renamed, sync the prompt, tools YAML, its `TOOL.md`, registry,
  `eval_base.json`, `eval_research_extension.json`, group eval where referenced,
  report, and demo text.

## Submission contents

Submit the complete `starter_v0/` including:

- `artifacts/system_prompt.md`, `artifacts/tools.yaml`, `artifacts/version_log.csv`,
  and `artifacts/REPORT.md`;
- `data/eval_group.json` (exactly 10 valid team cases);
- `runs/*.json`, `transcripts/*.transcript.json`, and optional `analysis/*.csv`;
- the new tool implementation/documentation/registration, UI code, and dependencies.

Never submit, commit, display, or screenshot `.env`, API keys, tokens, `.venv/`,
cache/build output. Keep Telegram credentials unset during *all* eval runs. Live send,
if used, is manual only after explicit confirmation and only to a private demo channel.

The instructor separately controls the final channel, filename convention, and
deadline; verify those before making the final ZIP or sharing a repository link.

## Bonus / optional scope

- UI is core, **not** bonus.
- Bonus requires the core UI plus **more than 3 additional new tools** written by the
  team. Built-in optional `send`, `policy`, `papers`, and `paper_text` do not count.
- Optional tools only need smoke tests when used in the group eval or demo. Leaving an
  unused optional declaration in YAML can still cause routing mistakes; remove it from
  the declaration/prompt for strict core isolation (then do not run extension eval).

## Working cadence

1. Preflight provider and smoke-test required APIs/tool.
2. Run v0; inspect evidence.
3. Form one hypothesis, make one targeted prompt/tool-declaration change, run v1,
   record it; repeat for v2 and v3.
4. Complete the 10 team evals, UI, demo rehearsal, reports, and final secret scan.

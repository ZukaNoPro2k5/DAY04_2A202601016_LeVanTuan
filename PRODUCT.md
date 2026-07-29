# Product

## Register

product

## Users

Lê Văn Tuấn uses the console to run and explain the research agent during a
bright-classroom showdown. Other student teams and instructors use it to
inspect responses, tool choices, arguments, results, errors, and version
evidence from a projected screen.

## Product Purpose

Research Agent Console makes the agent's behavior observable. It combines a
live multi-turn chat with a legible tool trace and stored v0-v3 evaluation
evidence, so a viewer can understand both what the agent answered and why a
specific artifact version produced that behavior.

Success means a new viewer can submit a scenario, identify every tool call and
its outcome, and compare the same eval case across versions without opening raw
JSON files or learning the codebase first.

## Brand Personality

Precise, calm, evidence-first. The interface should feel technically credible
without becoming theatrical, intimidating, or visually sterile.

## Anti-references

- Default Streamlit pages that look like uncomposed rows of widgets.
- Dense terminal consoles that make non-technical viewers parse raw JSON first.
- SaaS dashboards built from repetitive rounded cards and decorative metrics.
- AI-tool clichés such as purple gradients, glass panels, and glowing controls.

## Design Principles

1. Keep evidence beside the claim: response and trace remain visible together.
2. Make the current state explicit: provider, artifact version, waiting state,
   errors, and transcript identity are never ambiguous.
3. Reveal detail progressively: summarize tool outcomes first and keep raw JSON
   available on demand.
4. Optimize for the room: prioritize projector legibility and fast live-demo
   recovery over decorative density.
5. Treat external actions and secrets conservatively by default.

## Accessibility & Inclusion

Target WCAG 2.1 AA. Body copy and controls must maintain readable contrast,
keyboard focus must remain visible, status cannot depend on color alone, and
all non-essential motion must honor `prefers-reduced-motion`.

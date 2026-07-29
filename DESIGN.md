---
name: Research Agent Console
description: A calm evidence-first console for live research-agent demos.
tokens:
  color:
    canvas: "oklch(1 0 0)"
    surface: "oklch(0.968 0.008 180)"
    surface-strong: "oklch(0.935 0.014 180)"
    ink: "oklch(0.205 0.018 180)"
    muted: "oklch(0.44 0.025 180)"
    border: "oklch(0.84 0.018 180)"
    primary: "oklch(0.50 0.10 180)"
    primary-deep: "oklch(0.42 0.095 180)"
    success: "oklch(0.48 0.12 145)"
    warning: "oklch(0.62 0.13 75)"
    error: "oklch(0.49 0.17 25)"
  radius:
    small: "6px"
    medium: "12px"
  motion:
    state-change: "180ms"
---

# Design System: Research Agent Console

## Overview

**Creative North Star: "The Projected Lab Bench"**

The interface is designed for a bright classroom where a student operates a
laptop connected to a projector and viewers at the back need to follow the
agent's reasoning. It is restrained, precise, and task-led. Evidence remains
close to the response, while low-level detail is available progressively.

It explicitly rejects default Streamlit composition, dense terminal output,
repetitive SaaS card grids, and decorative AI-tool effects.

**Key Characteristics:**

- High-contrast light surfaces
- Response and tool evidence visible together
- Restrained state-driven motion
- Compact metadata with generous reading space
- Familiar product controls with visible focus

## Colors

True white carries the room-facing canvas. A weathered teal anchors actions,
focus, and selected state; status colors appear only where they communicate
meaning. The implementation uses only OKLCH color values so lightness and
contrast remain predictable:

- Canvas `oklch(1 0 0)`, surface `oklch(0.968 0.008 180)`, strong surface
  `oklch(0.935 0.014 180)`.
- Ink `oklch(0.205 0.018 180)`, muted ink `oklch(0.44 0.025 180)`, border
  `oklch(0.84 0.018 180)`.
- Primary `oklch(0.50 0.10 180)` with deep state
  `oklch(0.42 0.095 180)`.
- Success `oklch(0.48 0.12 145)`, warning `oklch(0.62 0.13 75)`, and error
  `oklch(0.49 0.17 25)`, always paired with a text label.

**The Ten Percent Rule.** Saturated color occupies no more than ten percent of
the screen; its rarity makes state changes easier to see.

## Typography

Use one technical-humanist system sans family for headings, body, labels, and
controls. Use the platform monospace stack only for arguments, results, hashes,
and transcript identifiers. Body and controls use at least 16px. Metadata and
JSON use 13–14px with a 1.5 line-height. Headings use compact 650–750 weights
and restrained negative tracking only at the page-title scale.

**The Projection Rule.** Body text never falls below 16px and trace JSON never
falls below 13px in the desktop classroom layout.

## Elevation

The system is flat by default. Depth comes from tonal surface changes and
structural dividers; shadows appear only for transient state such as a focused
popover, never as decoration.

**The Flat Bench Rule.** If a resting panel needs a large shadow to separate
from the page, its tonal hierarchy is wrong.

## Components

- **Header:** one title, one explanatory sentence, and compact runtime badges.
  Badges communicate metadata rather than behaving like decorative cards.
- **Sidebar:** read-only runtime configuration, boolean API readiness, safe
  Telegram boundary, session reset, transcript ID, and download action.
- **Conversation:** native Streamlit chat messages in a bounded reading region.
  Empty state includes three rehearsed prompts; desktop prompts share one row
  and mobile prompts stack.
- **Tool trace:** a selected-turn summary followed by one expander per round.
  Each tool event exposes its name, state, arguments, item count, result or
  error, with long JSON truncated.
- **Evidence comparison:** one compact metric table, one fixed-case selector,
  and one expander per stored artifact version. Failed versions open by default.
- **Controls:** 6px corner radius, minimum 40px height, clear text labels, and a
  3px teal `:focus-visible` ring with 2px offset.
- **Responsive layout:** the live workspace uses a 60/40 split above 760px and
  stacks conversation before trace at or below 760px. No horizontal scrolling
  is allowed.
- **Motion:** state transitions use 180ms. `prefers-reduced-motion` reduces
  transitions and animations to effectively zero.

## Do's and Don'ts

### Do:

- **Do** keep final responses and tool trace visible in the same viewport.
- **Do** use text labels with every success, waiting, and error state.
- **Do** expose raw JSON only through progressive disclosure.
- **Do** retain visible keyboard focus and reduced-motion behavior.

### Don't:

- **Don't** ship a default Streamlit page that looks like uncomposed widgets.
- **Don't** turn the trace into a dense terminal wall.
- **Don't** build repetitive rounded SaaS cards or decorative metrics.
- **Don't** use purple gradients, glass panels, glowing controls, or gradient text.
- **Don't** use side-stripe accents or cards with radii above 16px.

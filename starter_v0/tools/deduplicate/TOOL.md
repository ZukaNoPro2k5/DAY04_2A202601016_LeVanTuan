---
name: deduplicate
track: team
kind: local
requires_env: []
inputs: [items]
outputs: [input_count, removed_count, items]
side_effect: false
---

# deduplicate

Removes duplicate research results from an existing list.

Items are considered duplicates by canonicalized URL. Tracking parameters and
URL fragments are ignored. When no URL is available, normalized titles are
used instead.

The tool preserves the first occurrence and the original order of the
remaining items. It does not search the web, fetch URLs, or format a digest.
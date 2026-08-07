# Plan: A3 humanizer + fact hash guard

**Date:** 2026-08-07  
**Status:** Implemented on `cursor/a3-humanizer-0af3`  
**Origin:** build-spec v2 §A3 + architect review gate (“show me the test that proves the humanizer cannot change a templated fact”)

## Goal

Turn correct generated pages into customer-readable pages without ever letting
“enjoyable” edit a templated fact.

## Approach

1. Ownable style guide: `style/customer-voice.md` (ten rules).
2. `pipelines/write_prose.py` drafts Overview prose; uncertain details become `<!-- TODO -->`.
3. `pipelines/humanize.py` rewrites prose sections only against the style guide.
4. Generators stamp `<!-- section:prose -->` / `<!-- section:facts -->` markers.
5. `fact_hash` + `guarded_transform` refuse any transform that alters the facts block.

## Out of scope

Nightly improvement loop (A4), live Tempo agent evals (B1+), LLM-backed prose
(deterministic offline rules for V0; style file remains the voice contract).

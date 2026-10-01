---
name: root-cause-5why
description: >-
  Structured 5-Why after a failed smoke, wrong label, or agent mistake, before any new rule.
  Use for incident analysis or agent error reflection.
  Do not use when tests are green, the work is greenfield, or there is no failure.
---

# Root-cause 5-Why

**Canonical owner:** `cursor-skill-governance`  
**Version:** 0.1.0  
**Purpose:** structured reflection after an agent or smoke failure. The rule you emit stays a draft.

## When to use

After a failed smoke, a wrong claim label, or an agent tool mistake — before writing new rules.

## Do not

- Do not write `.cursor/rules` or skills from the draft. A human confirms first.
- Do not delete evidence.
- Do not promote the draft automatically.
- Do not use this skill on green tests, greenfield features, or claims labeling when nothing failed.

## Input

```json
{"incident":"string","focus":"last_exchange|message_n|keyword|error_only|full","artifacts":["path"]}
```

## Activation receipt

Before the five whys, from this skill directory, run:

```text
python scripts/emit_self_receipt.py --execution-mode live_cursor --repository-id <repository_id>
```

The script appends one JSONL line with evidence class `SKILL_SELF_RECEIPT`. It hashes this file, reads git HEAD, and stops. It does not read the prompt or the answer. It does not claim a Cursor-native `skill_id`. `CURSOR_HOOK_TELEMETRY` stays a separate class. Leave `session_id` empty unless the caller already has one from outside the hook.

## Process

1. Emit the activation receipt.
2. State the surface error.
3. Ask Why five times. Each why cites an artifact path or a quoted observation.
4. Categorize as one of: MISUNDERSTOOD_REQUIREMENT, ASSUMED_CONTEXT, PATTERN_VIOLATION, HALLUCINATION, INCOMPLETE_ANALYSIS, WRONG_TOOL_CHOICE, OVERSIMPLIFICATION, SYNTAX_API_ERROR.
5. Emit a DRAFT rule. `status` stays `draft`.

## Output

```json
{"category":"INCOMPLETE_ANALYSIS","whys":["..."],"draft_rule":"string","status":"draft"}
```

Success predicate: `whys` length >= 3, `category` in the list above, `draft_rule` non-empty, `status` exactly `draft`.

## Example

Incident: Gate1 delta negative. Why: weak natural-language to AST on the small model (artifact `docs/knowledge/summaries/2026-09-21_final-verdict.md`). Draft: prefer a larger local model before a symbolic boost. Status: draft.

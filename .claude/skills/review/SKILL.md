---
name: review
description: Step-by-step procedure to review an uncommitted diff inside /mnt/workspace/repo/ against the GitHub issue and the exploration + implementation artifacts. Produces /mnt/workspace/artifacts/reviewing.json with approved, issues[], scope_creep[]. Use whenever a pipeline task is reviewing.
---

# Review

## Inputs
- User message: may be as short as "Review the uncommitted diff."
- Artifacts: `/mnt/workspace/artifacts/exploring.json`, `/mnt/workspace/artifacts/implementing.json`.
- Working tree: `/mnt/workspace/repo/` with uncommitted changes.

## Output
- **Always**: `/mnt/workspace/artifacts/reviewing.json`.

## Procedure

### 1. See what changed
```bash
git -C /mnt/workspace/repo status --porcelain
git -C /mnt/workspace/repo diff
```

### 2. Check against intent
- Re-read the issue summary from `exploring.json`.
- Re-read `implementing.json.summary` and `files_changed`.
- Ask yourself:
  - Does the diff actually address the issue? (Missing an acceptance criterion is a blocker.)
  - Are files changed that aren't in `implementing.json.files_changed`? That's either a sneaky fix or scope creep — flag it.
  - Are there obvious bugs, exceptions, or broken imports?
  - Are there hard-coded secrets, debug `print` statements, TODOs left behind?
  - Does new code follow the repo's existing conventions?
  - If tests exist for this surface area, were they updated?

### 3. Be terse and specific
Each item in `issues[]` must be a concrete, one-sentence fix. Not "consider improving error handling" but "line 42 in app.py catches `Exception` — narrow to `KeyError`".

### 4. Emit the artifact
Write `/mnt/workspace/artifacts/reviewing.json`:

```json
{
  "approved": true,
  "issues": [
    "app.py:42 — catch KeyError specifically instead of bare Exception.",
    "Add a test for the new /healthz route in tests/test_routes.py."
  ],
  "scope_creep": [
    "README.md line 15: formatting change unrelated to the issue."
  ],
  "summary": "Two actionable issues, one minor scope-creep. Not approved."
}
```

`approved` is `true` iff `issues[]` is empty OR all items are optional nits the reviewer explicitly marks with `(nit:)` prefix. If `approved: false`, the implementer will read `issues[]` and re-roll.

## Guardrails
- **Read-only.** Never `Write` or `Edit` anything inside `repo/`. The only `Write` allowed is the artifact file.
- **Bash is git-only here.** `git status`, `git diff`, `git log`, `git show` — nothing else.
- Don't rerun tests (the implementer already did). If tests look missing for a surface area, flag it in `issues[]`.
- Don't fabricate problems. A clean diff deserves `approved: true`.

## Final response
Return ONE line: the `summary` field from the artifact. Nothing else.

---
name: implement
description: Step-by-step procedure to implement a GitHub issue inside /mnt/workspace/repo/ using the exploration artifact as grounding. Makes minimal-diff code changes, optionally runs the repo's standard test command, and emits /mnt/workspace/artifacts/implementing.json. Use whenever a pipeline task is implementing (first pass) or re-implementing (after a reviewer bounce).
---

# Implement

## Inputs
- User message: the GitHub issue + comments, plus the latest `exploring.json`. On retry iterations the user message also includes `reviewing.json.issues[]` — a list of things to fix.
- Working directory: `/mnt/workspace/repo/`.

## Outputs
- **Always**: `/mnt/workspace/artifacts/implementing.json`.
- **Code changes**: applied in place under `/mnt/workspace/repo/` (uncommitted).
- **Conditional**: `/mnt/workspace/clarify.md` if a new ambiguity blocks progress.

## Procedure

### 1. Anchor scope
- Read `exploring.json` — take `files_of_interest` as the starting set, `test_command` as the test runner.
- Read the issue + comments once more and write down, in one sentence, the acceptance criterion.

### 2. Implement minimally
- Edit only the files required to meet the acceptance criterion.
- Follow the repo's existing conventions (naming, layout, error handling) — grep for similar patterns before introducing new ones.
- **Do not**: rename unrelated files, reformat unrelated code, add new dependencies unless strictly required, refactor "while you're in there."
- If a change needs a new file, place it where the repo puts similar files (same parent directory as the examples you found in `files_of_interest`).

### 3. Handle mid-flight ambiguity
If you encounter a question the issue doesn't resolve and `exploring.json` didn't already raise:
1. Save what you have as in-progress (don't finish the change).
2. Write the question(s) one-per-line to `/mnt/workspace/clarify.md`.
3. Set `needs_clarification: true` in the artifact, list the questions, and stop.

### 4. Run tests (only if obvious)
Decide the test command from `exploring.json.test_command`. Accept only these canonical forms:
- `pytest` / `pytest <path>`
- `npm test` / `yarn test` / `pnpm test`
- `go test ./...`
- `cargo test`
- `make test` (if a `Makefile` with a `test` target exists)

If none match, **don't run anything**. Record `tests_run: null, tests_passed: null`.

If you run tests and they fail on code you didn't touch, don't chase the failures — note them in `implementing.json.notes`.

### 5. Emit the artifact
Write `/mnt/workspace/artifacts/implementing.json`:

```json
{
  "approved": false,
  "needs_clarification": false,
  "questions": [],
  "files_changed": ["relative/path/from/repo/root.py"],
  "summary": "One sentence: what changed and why it satisfies the issue.",
  "tests_run": "pytest" ,
  "tests_passed": true,
  "notes": "Optional free-form — surprises, flaky tests skipped, etc."
}
```

## Guardrails
- Edit exclusively inside `/mnt/workspace/repo/`. Artifacts and `clarify.md` go to `/mnt/workspace/` sibling paths.
- **Never** run `git commit`, `git push`, `git checkout -b`, `git reset`, or touch anything under `.git/`. VCS is the PR subagent's job.
- **Never** install packages globally. If a dep is truly required, add it to the repo's manifest (`pyproject.toml` / `package.json` / etc.) — but prefer not to.
- **Never** print secrets, tokens, or env vars.

## Final response
Return ONE line: the `summary` field from the artifact. Nothing else.

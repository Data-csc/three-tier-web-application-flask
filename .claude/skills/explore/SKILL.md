---
name: explore
description: Step-by-step procedure to explore an unfamiliar repository for a GitHub issue — map the codebase, locate the files the issue touches, surface ambiguities that block implementation, and emit a structured artifact at /mnt/workspace/artifacts/exploring.json. Use whenever a pipeline task begins with an unfamiliar repo + an issue description.
---

# Explore

## Inputs
- User message: GitHub issue title, body, and comments.
- Working directory: `/mnt/workspace/repo/` (the cloned target repo).

## Outputs
- **Always**: `/mnt/workspace/artifacts/exploring.json` (schema below).
- **Conditional**: `/mnt/workspace/clarify.md` — one line per question — ONLY when you cannot proceed without a human answer.

## Procedure

### 1. Establish project shape (5 min budget)
- Read, if present: `README*`, `CONTRIBUTING*`, `ARCHITECTURE*`, top-level `docs/` index.
- Read whichever of these exists: `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `Gemfile`, `Makefile`, `Dockerfile`.
- Glob for entry points: `main.*`, `index.*`, `app.*`, `server.*`, `cmd/*/main.go`, `src/main/*`, `bin/*`.
- From the config files and tree, infer: language, framework, where source lives, where tests live, what the standard test command is (save it for the implementer).

### 2. Locate the issue's surface area
- Extract nouns / identifiers from the issue body (route names, class names, file paths, error strings).
- For each, run `rg -n "<term>" /mnt/workspace/repo` and read the top 2–3 hits with ~20 lines of surrounding context.
- Build a list of files the change is likely to touch. Don't be exhaustive — 3–8 files is plenty.

### 3. Find blockers
Enumerate every question you cannot answer from the code + issue alone. Good examples:
- "The issue says 'add caching' — what TTL? Which keys?"
- "Two existing models have similar names; which one does the issue mean?"
- "The issue references `utils.py` but there are three files with that name."

Bad examples (don't ask these — resolve them yourself):
- Style preferences the repo already establishes.
- Trivially checkable things (`ls`, `cat`, `git log`).

### 4. Emit the artifact
Write `/mnt/workspace/artifacts/exploring.json` (create the directory if it doesn't exist):

```json
{
  "approved": false,
  "needs_clarification": false,
  "questions": [],
  "summary": "One sentence describing what the issue asks and where the change belongs.",
  "files_of_interest": ["relative/path/from/repo/root.py"],
  "entry_points": ["app.py"],
  "test_command": "pytest" ,
  "language": "python",
  "framework": "flask | react | spring | null"
}
```

If there are blockers: set `needs_clarification: true`, fill `questions`, AND write one question per line to `/mnt/workspace/clarify.md`.

## Guardrails
- **Never** `Write` or `Edit` anything under `/mnt/workspace/repo/`. All outputs land in `/mnt/workspace/` sibling paths.
- **Never** run `git`, `npm`, `pip`, `make`, or other state-mutating commands. Read-only shell: `ls`, `cat`, `rg`, `grep`, `head`, `find`, `file`.
- **Never** guess at values just to fill the artifact. `null` / empty lists are honest.
- Stop after you have enough to decide "go / clarify" — do not exhaustively catalogue the whole repo.

## Final response
Return ONE line to the parent conversation: the `summary` field from the artifact. Nothing else.

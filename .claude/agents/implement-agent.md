---
name: implement-agent
description: Implements the feature or applies critique fixes
model: sonnet
permissionMode: dontAsk
hooks:
  Stop:
    - command: "./.claude/hooks/subagent-stop.sh implement"
---

Read in this order:
1. ./.dev-claude/project.json
2. ./.dev-claude/issue.json     (full issue spec + comments, pre-fetched — do NOT call get_issue via MCP)
3. ./.dev-claude/explore.md
4. ./.dev-claude/questions.md   (if present — contains answered clarifications)
5. ./.dev-claude/critique.md    (if present — this is a re-implementation pass)

Call mcp__gateway__GitHub___set_labels with `labels: ["stage:implementing"]` at the start.

FIRST RUN (no critique.md exists):
  - Create branch: `git checkout -b feat/issue-{number}`
    If the branch already exists: `git checkout feat/issue-{number}`
  - Implement the feature, following patterns from explore.md exactly
  - Run the test command from explore.md — fix any failures before committing
  - `git add -A && git commit -m "feat: {description} (#{number})"`

SECOND RUN (critique.md exists):
  - You are already on feat/issue-{number}
  - Address every point raised in critique.md before touching anything else
  - Run tests again — fix failures
  - `git add -A && git commit -m "fix: apply critique (#{number})"`

AFTER COMMITTING — UPDATE CLAUDE.md IF NEEDED:
If your changes affected any of the following, update ./.claude/CLAUDE.md to match:
  - New or changed dependencies (e.g. added pytest to requirements.txt)
  - New directories or changed project structure
  - Changed test command or test setup
  - New conventions introduced (e.g. new middleware pattern, new config approach)
If CLAUDE.md was updated, include it in the same commit (amend or new commit).

Do not push. Do not open a PR. Exit after committing.
Do not modify files outside the feature scope.
Do not add dependencies not explicitly required by the spec.

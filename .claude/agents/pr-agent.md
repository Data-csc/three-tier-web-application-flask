---
name: pr-agent
description: Pushes the branch and creates the pull request
tools:
  - Read
  - Write
  - Bash(git push:*)
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git rev-parse:*)
  - mcp__gateway__GitHub___create_pull_request
  - mcp__gateway__GitHub___set_labels
  - mcp__gateway__GitHub___comment_on_issue
model: sonnet
permissionMode: dontAsk
hooks:
  Stop:
    - command: "./.claude/hooks/subagent-stop.sh pr"
---

Read:
- ./.dev-claude/project.json
- ./.dev-claude/critique.md   (was there a critique?)
- Run `git log main...HEAD`  (commits made)

STEP 1: `git push origin feat/issue-{number}`

STEP 2: Write ./.dev-claude/pr.md summarising what was built.

STEP 3: Call mcp__gateway__GitHub___create_pull_request:
  owner and repo from project.json
  title: "feat: {issue title} (#{number})"
  head: feat/issue-{number}
  base: main
  draft: false
  body:
    ## What
    One paragraph describing what was built.

    ## Why
    Closes #{number}

    ## How
    Key implementation decisions and patterns used.

    ## Testing
    How to verify the change works.

STEP 4: Call mcp__gateway__GitHub___set_labels with `labels: ["state:pr-created"]`

On push/PR failure: retry once. On second failure, call mcp__gateway__GitHub___set_labels
with `labels: ["state:failed"]` and post an error comment via
mcp__gateway__GitHub___comment_on_issue.

Exit cleanly. `state:pr-created` is the terminal success state.

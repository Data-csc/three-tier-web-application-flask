---
name: pr-agent
description: Pushes the branch and creates the pull request
model: sonnet
permissionMode: dontAsk
hooks:
  Stop:
    - command: "./.claude/hooks/subagent-stop.sh pr"
---

Read:
- ./.dev-claude/project.json
- ./.dev-claude/issue.json    (for issue title + number — do NOT call get_issue via MCP)
- ./.dev-claude/critique.md   (was there a critique?)
- Run `git log main...HEAD`  (commits made)

STEP 1: `git push origin feat/issue-{number}`

STEP 2: Write ./.dev-claude/pr.md summarising what was built. Then post pr.md content
as a comment on the issue via mcp__gateway__GitHub___comment_on_issue
(use owner, repo, issue_number from project.json). Prefix with `### 📦 PR Summary\n\n`.

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

  CRITICAL — the `body` field is a plain markdown string. Do NOT use:
    - shell substitution like $(...) or $(cat <<EOF ... EOF)
    - heredoc syntax (<<EOF, <<'EOF')
    - command chaining (&&, ;)
  WAF blocks these patterns with HTML 403. If you see that, simplify the body
  (strip backticks around paths, remove code fences, shorten) and retry.

STEP 4: Call mcp__gateway__GitHub___set_labels with `labels: ["state:pr-created"]`

On push/PR failure: retry once. On second failure, call mcp__gateway__GitHub___set_labels
with `labels: ["state:failed"]` and post an error comment via
mcp__gateway__GitHub___comment_on_issue.

Exit cleanly. `state:pr-created` is the terminal success state.

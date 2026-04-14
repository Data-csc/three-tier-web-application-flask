---
name: pr
description: Step-by-step procedure to create a branch, commit the implementer's uncommitted changes, push, and open a pull request via gh. Emits /mnt/workspace/artifacts/creating-pr.json. Use whenever a pipeline task is creating-pr.
---

# PR

## Inputs
- User message: branch name hint (e.g. `agent/issue-42`), base branch (default `main`), issue number + title.
- Artifacts: `/mnt/workspace/artifacts/implementing.json`, `/mnt/workspace/artifacts/reviewing.json`.
- Working tree: `/mnt/workspace/repo/` with uncommitted implementer changes.
- Pre-configured auth: `GITHUB_TOKEN` env var (or git credential helper) set by the runtime container.

## Output
- **On success**: `/mnt/workspace/artifacts/creating-pr.json` with `pr_url`, `branch`, `commit_sha`.
- **On failure**: same file with `error` field, and exit with non-zero shell exit code.

## Procedure

### 1. Sanity check
```bash
cd /mnt/workspace/repo
git status --porcelain       # must show uncommitted changes
git rev-parse --abbrev-ref HEAD   # must NOT already be on agent/issue-*
```
If the working tree is clean, exit with an error artifact — nothing to PR.

### 2. Create the branch
Use the branch name from the prompt. If it collides with an existing local or remote branch, append `-retry-<N>` where `N` is the smallest integer that makes it unique.
```bash
git checkout -b "$BRANCH_NAME"
```

### 3. Commit
Subject line: the GitHub issue title, truncated to 72 chars. Body: bullet list from `implementing.json.summary` + `files_changed`, plus a `Closes #<N>` trailer.

```bash
git add -A
git commit -m "$SUBJECT" -m "$BODY"
```

### 4. Push
```bash
git push -u origin HEAD
```

If push fails:
- Auth error → write `{"error": "push auth failed: <last line of stderr>"}` to the artifact, exit 1.
- Non-fast-forward → never force-push. Write `{"error": "branch exists with different history"}`, exit 1.

### 5. Open the PR
```bash
gh pr create \
  --title "$SUBJECT" \
  --body "$PR_BODY" \
  --base "${BASE:-main}" \
  --head "$BRANCH_NAME"
```

PR body template:
```markdown
## Summary
<implementing.json.summary>

## Files changed
- <file 1>
- <file 2>

## Review notes
<reviewing.json.summary>

Closes #<ISSUE_NUMBER>

---
🤖 Opened by the automated DevOps pipeline.
```

Capture the URL from `gh` stdout (`gh pr create` prints it on success).

### 6. Emit the artifact
Write `/mnt/workspace/artifacts/creating-pr.json`:

```json
{
  "pr_url":     "https://github.com/Data-csc/repo/pull/42",
  "branch":     "agent/issue-42",
  "commit_sha": "a1b2c3d4…",
  "base":       "main"
}
```

## Guardrails
- **Never force-push.** No `-f`, `--force`, `--force-with-lease`.
- **Never `git commit --amend`.** Every run creates a fresh commit on a fresh branch.
- **Never push to `main` / `master` / any protected branch.** If the CLI somehow lands you there, bail out with `{"error": "refused to push to protected branch"}`.
- **Don't print secrets.** Redact `GITHUB_TOKEN` if it appears in any command or output.
- **No code edits in this phase.** If `git status` shows files other than those in `implementing.json.files_changed`, that's suspicious — log it but proceed.

## Final response
Return ONE line:
- Success: the PR URL.
- Failure: `ERROR: <one-line reason>`.

# `.claude/` — DevOps pipeline agents + skills

This directory wires the repository into an automated GitHub-issue-to-PR pipeline. It is **generic**: the same `.claude/` tree can be dropped into any repository and the pipeline will work without edits. Nothing inside references a specific language or framework.

## What's here

```
.claude/
├── agents/
│   ├── explorer.md       ← phase 1: understand the issue
│   ├── implementer.md    ← phase 2: write the code
│   ├── reviewer.md       ← phase 3: critique the diff
│   └── pr-opener.md      ← phase 4: commit + push + open PR
└── skills/
    ├── explore/SKILL.md
    ├── implement/SKILL.md
    ├── review/SKILL.md
    └── pr/SKILL.md
```

Each **agent** runs in its own Claude context window with a specific tool allowlist; the linked **skill** (via `skills:` frontmatter) is injected on entry. This keeps phases isolated — the implementer never sees the exploration noise, the reviewer never sees the implementation reasoning, etc.

## How the pipeline invokes them

The orchestrator (`lambda_temp.py` → full version in `stages/06-lambda-orchestrator.md`) runs these commands inside the AgentCore Runtime session:

```bash
cd /mnt/workspace/repo && claude -p "<issue>" --agent explorer    --max-turns 8  --output-format json
cd /mnt/workspace/repo && claude -p "<issue+exploration>"  --agent implementer --max-turns 25
cd /mnt/workspace/repo && claude -p "Review the uncommitted diff." --agent reviewer    --max-turns 5  --output-format json
cd /mnt/workspace/repo && claude -p "Branch name hint: agent/issue-<N>. Base: main." --agent pr-opener --max-turns 10
```

## Filesystem contract

```
/mnt/workspace/
├── repo/                 ← this repository (cloned by Lambda)
├── clarify.md            ← written by an agent when it needs user input (pipeline pauses)
└── artifacts/
    ├── exploring.json
    ├── implementing.json
    ├── reviewing.json
    └── creating-pr.json
```

**Code changes land only under `repo/`.** Everything else — questions for the user, structured skill outputs — lives alongside it so the eventual PR diff stays clean.

The pipeline pauses if any phase writes `/mnt/workspace/clarify.md`. The Status Agent posts those questions as a comment on the GitHub issue, moves the project board back to Todo, and waits. When the user answers and moves the board back to In Progress, the pipeline resumes from `paused_at_stage`.

## Prerequisites for the container

- `claude` CLI installed (via `claude.ai/install.sh`).
- `git` available.
- `gh` CLI available, authenticated with a token that can push to the repo and open PRs (via `GITHUB_TOKEN` env or a credential helper).
- `/mnt/workspace` mounted as AgentCore Persistent Filesystems.

## Reuse in another repo

Copy `.claude/` as-is. The agents and skills only reference paths under `/mnt/workspace/` (absolute) and relative paths inside the repo (`README*`, `package.json`, …) that are discovered dynamically. No language-specific assumptions.

## Extending

- **Tune the skills** for this repo by adding a `CLAUDE.md` at the repo root — agents pick it up automatically and it augments without overriding the skill body.
- **Change a tool allowlist**: edit the `tools:` frontmatter field on the matching agent file.
- **Add a phase**: create a new agent + skill pair and wire it into `flow.md` / the orchestrator.

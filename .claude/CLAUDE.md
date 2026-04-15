# dev-claude project context — three-tier-web-application-flask

## Stack
- Python 3 / Flask (ApplicationLayer)
- Static HTML/JS (WebLayer)
- CloudFormation templates (cfn-stacks/)
- pytest for tests

## Conventions
- App code lives under `ApplicationLayer/`
- Web assets under `WebLayer/`
- CFN in `cfn-stacks/`
- Python: snake_case, 4-space indent, no trailing whitespace

## Test command
```
cd ApplicationLayer && pytest -q
```
(If `ApplicationLayer/requirements.txt` lists test deps, install with `pip install -r ApplicationLayer/requirements.txt` first.)

## Rules
- Branch naming: `feat/issue-{number}`
- Commit format: `feat: {description} (#{number})`
- Never add dependencies not explicitly required by the spec
- Never modify files outside the feature scope
- Never leave debug statements or commented-out code
- Always run tests before committing — fix failures, do not skip

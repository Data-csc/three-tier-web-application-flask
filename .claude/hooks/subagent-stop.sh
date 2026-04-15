#!/bin/bash
# Logging-only hook. Label transitions happen inside each subagent via MCP.
STAGE=$1
ISSUE_NUM=$(jq -r '.issue_number' ./.dev-claude/project.json 2>/dev/null || echo "unknown")
echo "[dev-claude] subagent-stop stage=$STAGE issue=#$ISSUE_NUM ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

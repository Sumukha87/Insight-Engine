#!/bin/bash
# PreToolUse hook: Block all git write commands.
# Git is user-only — Claude must never add, commit, push, reset, or rebase.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))")

if echo "$COMMAND" | grep -qE '^\s*git\s+(add|commit|push|reset|rebase|checkout\s+--|restore|clean|stash|tag|branch\s+-[dD]|merge|cherry-pick|am|format-patch)'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Git write commands are blocked. Only the user manages git. See CLAUDE.md: Git is user-only.'}}))"
  exit 0
fi

if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Force push blocked. Git is user-only.'}}))"
  exit 0
fi

exit 0

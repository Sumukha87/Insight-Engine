#!/bin/bash
# PreToolUse hook: Warn/block /mnt/c/ paths — use WSL2 native paths only.

INPUT=$(cat)
CHECK_STRING=$(echo "$INPUT" | python3 -c "
import sys,json
d = json.load(sys.stdin).get('tool_input',{})
print(d.get('command','') + ' ' + d.get('file_path',''))
")

if echo "$CHECK_STRING" | grep -qE '/mnt/c/|/mnt/d/'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Blocked: /mnt/c/ path detected. Use WSL2 native paths (/home/\$USER/) — Docker volumes on /mnt/ have severe I/O penalties.'}}))"
  exit 0
fi

exit 0

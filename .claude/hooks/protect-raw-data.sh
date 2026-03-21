#!/bin/bash
# PreToolUse hook: Block direct writes to data/raw/ (DVC-managed, never modify directly).

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))")

if echo "$FILE_PATH" | grep -qE '/data/raw/'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Cannot write to data/raw/ — raw data is DVC-managed and immutable. All ingestion goes through DVC pipelines.'}}))"
  exit 0
fi

exit 0

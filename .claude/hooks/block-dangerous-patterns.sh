#!/bin/bash
# PreToolUse hook (Edit|Write): Block dangerous code patterns — eval, exec, pickle on user input,
# dangerouslySetInnerHTML, disabled security checks.

INPUT=$(cat)
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin).get('tool_input', {})
print(d.get('new_string', '') + ' ' + d.get('content', ''))
")

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
")

# Skip docs, hooks, skills, config
if echo "$FILE_PATH" | grep -qE '(\.claude/|docs/|CLAUDE\.md|\.md$|\.json$|\.yml$|\.yaml$)'; then
  exit 0
fi

# Block eval() and exec() in Python (except safe known uses like ast.literal_eval)
if echo "$CONTENT" | grep -qE '\beval\s*\(' | grep -v 'literal_eval'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: eval() detected. Never use eval() — it executes arbitrary code. Use ast.literal_eval() for safe parsing, or json.loads() for JSON.'}}))"
  exit 0
fi

# Block dangerouslySetInnerHTML without sanitization
if echo "$CONTENT" | grep -qE 'dangerouslySetInnerHTML'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: dangerouslySetInnerHTML detected. This enables XSS attacks. Use React default escaping. If raw HTML is required, sanitize with DOMPurify first.'}}))"
  exit 0
fi

# Block pickle.loads on anything that could be user-controlled
if echo "$CONTENT" | grep -qE 'pickle\.(loads|load)\s*\('; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: pickle.loads() detected. Pickle deserialization can execute arbitrary code. Use json.loads() or a safe serialization format.'}}))"
  exit 0
fi

# Block subprocess.call/Popen with shell=True and user input
if echo "$CONTENT" | grep -qE 'subprocess\.(call|run|Popen)\(.*shell\s*=\s*True'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: subprocess with shell=True detected. This enables command injection. Use shell=False and pass args as a list.'}}))"
  exit 0
fi

exit 0

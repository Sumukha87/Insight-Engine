#!/bin/bash
# PreToolUse hook (Edit|Write): Block SQL string interpolation patterns.
# Enforces parameterized queries only — OWASP SQL Injection prevention.

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

# Only check Python and TypeScript source files
if ! echo "$FILE_PATH" | grep -qE '\.(py|ts|tsx)$'; then
  exit 0
fi

# Skip documentation, hooks, skills
if echo "$FILE_PATH" | grep -qE '(\.claude/|docs/|CLAUDE\.md|\.md$)'; then
  exit 0
fi

# Pattern: f-string or .format() with SQL keywords (SELECT, INSERT, UPDATE, DELETE, MATCH, MERGE)
if echo "$CONTENT" | grep -qE 'f["\x27](SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|MATCH|MERGE|CREATE INDEX|CALL)'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: SQL/Cypher string interpolation detected (f-string). Use parameterized queries: SQLAlchemy ORM, text() with bound params, or Cypher \$param syntax. See CLAUDE.md SECURITY section.'}}))"
  exit 0
fi

if echo "$CONTENT" | grep -qE '\.format\(\).*\b(SELECT|INSERT|UPDATE|DELETE|MATCH|MERGE)\b|\"(SELECT|INSERT|UPDATE|DELETE|MATCH|MERGE).*\{.*\}.*\"\.format'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: SQL .format() interpolation detected. Use parameterized queries only.'}}))"
  exit 0
fi

# Pattern: string concatenation with SQL keywords
if echo "$CONTENT" | grep -qE '"(SELECT|INSERT|UPDATE|DELETE)\s.*"\s*\+\s*(str\(|[a-z_]+)'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: SQL string concatenation detected. Use parameterized queries only.'}}))"
  exit 0
fi

exit 0

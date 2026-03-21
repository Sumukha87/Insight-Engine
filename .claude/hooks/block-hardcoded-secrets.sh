#!/bin/bash
# PreToolUse hook (Edit|Write): Block writes that contain hardcoded secrets, passwords, or credentials.
# Security is the top priority — no exceptions.

INPUT=$(cat)
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin).get('tool_input', {})
# Check both new_string (Edit) and content (Write)
print(d.get('new_string', '') + ' ' + d.get('content', ''))
")

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))
")

# Skip .env files and .env.example (these are supposed to have credential placeholders)
if echo "$FILE_PATH" | grep -qE '\.env(\.example)?$'; then
  exit 0
fi

# Skip hook scripts themselves and settings.json
if echo "$FILE_PATH" | grep -qE '\.claude/(hooks|settings)'; then
  exit 0
fi

# Skip CLAUDE.md and documentation files (rules reference secret patterns in examples)
if echo "$FILE_PATH" | grep -qE '(CLAUDE\.md|docs/.*\.md|SKILL\.md|progress\.md|architecture\.md|stack\.md|memory/.*\.md|MEMORY\.md)$'; then
  exit 0
fi

# Pattern: actual password/secret assignments in code (not env var lookups)
# Matches: password = "...", secret_key = "abc123", api_key="sk-..."
# Does NOT match: os.environ["SECRET_KEY"], process.env.SECRET_KEY, $POSTGRES_PASSWORD
if echo "$CONTENT" | grep -qiE '(password|secret_key|api_key|private_key|access_token|auth_token)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]'; then
  # Exclude lines that are env var lookups
  SUSPICIOUS=$(echo "$CONTENT" | grep -iE '(password|secret_key|api_key|private_key|access_token|auth_token)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]' | grep -viE '(os\.environ|os\.getenv|process\.env|getenv|environ\.get|\$\{|changeme|placeholder|example)')
  if [ -n "$SUSPICIOUS" ]; then
    python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: Hardcoded secret detected. Never put passwords, API keys, or tokens directly in code. Use os.environ[\"VAR\"] (Python) or process.env.VAR (TypeScript). See CLAUDE.md SECURITY section.'}}))"
    exit 0
  fi
fi

# Pattern: AWS keys, GitHub tokens, JWT secrets with real values
if echo "$CONTENT" | grep -qE '(AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,}|eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]+\.)'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'SECURITY VIOLATION: Real credential pattern detected (AWS key / GitHub token / API key / JWT). Never hardcode credentials. Use environment variables.'}}))"
  exit 0
fi

exit 0

#!/bin/bash
# PreToolUse hook: Block cloud API calls and pip install of cloud SDKs.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))")

if echo "$COMMAND" | grep -qE 'pip\s+install.*(openai|boto3|azure|google-cloud|anthropic)'; then
  python3 -c "import json; print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':'Blocked: No cloud spend. This project runs 100% locally — Ollama for LLM, nomic-embed-text for embeddings. No OpenAI/AWS/Azure.'}}))"
  exit 0
fi

exit 0

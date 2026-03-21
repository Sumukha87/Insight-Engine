#!/bin/bash
# SessionStart hook: Check that critical Docker services are running.
# Prints warnings if services are down — doesn't block.

REQUIRED_CONTAINERS="ie-neo4j ie-qdrant ie-mlflow ollama"
DOWN=""

for container in $REQUIRED_CONTAINERS; do
  if ! docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q "true"; then
    DOWN="$DOWN $container"
  fi
done

if [ -n "$DOWN" ]; then
  echo "⚠️  Docker services not running:$DOWN"
  echo "Run: docker compose up -d"
  # Non-blocking — exit 0 so session continues
fi

exit 0

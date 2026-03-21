# Feature Explainer

Explain how **$ARGUMENTS** works in the context of the Insight-Engine project.

The user does not have deep background knowledge of this technology. Explain it from scratch but always tie every concept back to how it is actually used in THIS project — not in general terms.

Structure your explanation as:

## What is $ARGUMENTS?
One paragraph. What it is, what problem it solves. No jargon.

## Why does Insight-Engine use it?
Explain specifically why this project needs it. What would break or be missing without it.

## How it fits into the project
Show exactly where it lives in the stack. Reference the actual files, ports, and services involved.
For example: "Airflow runs via `bash scripts/start_airflow.sh`, its DAG lives at `dags/insight_engine_pipeline.py`, and its UI is at localhost:8080."

## How to use it day-to-day
Step by step — what the user actually does with it. Start commands, UI walkthrough, common operations. Be specific to this project.

## How it connects to other parts
Explain what it talks to. For example: "Airflow triggers the NER pipeline which writes to data/processed/, which Neo4j then reads from."

## What could go wrong
2–3 common issues the user might hit and how to fix them, specific to this setup (WSL2, Docker, RTX 4060).

Keep language simple. Use analogies where helpful. Always reference real files and commands from this project.

#!/bin/bash
# Start Airflow for Insight-Engine pipeline monitoring
# Usage: bash scripts/start_airflow.sh
# UI: http://localhost:8080  (admin / admin)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export AIRFLOW_HOME="$PROJECT_ROOT/.airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$PROJECT_ROOT/dags"
export AIRFLOW__CORE__EXECUTOR=SequentialExecutor
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite:///$PROJECT_ROOT/.airflow/airflow.db"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__WEBSERVER__SECRET_KEY="insight-engine-local-dev"
export AIRFLOW__CORE__FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null || echo 'insight-engine-fernet-key-placeholder-32ch')"

source "$PROJECT_ROOT/.venv/bin/activate"

echo "Airflow home: $AIRFLOW_HOME"
echo "DAGs folder:  $AIRFLOW__CORE__DAGS_FOLDER"

# First-time init (safe to re-run)
airflow db migrate --quiet 2>/dev/null || airflow db init

# Create admin user if it doesn't exist
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@insight-engine.local 2>/dev/null || true

echo ""
echo "Starting Airflow..."
echo "UI: http://localhost:8080"
echo "Login: admin / admin"
echo ""

# standalone starts webserver + scheduler in one process (dev mode)
airflow standalone

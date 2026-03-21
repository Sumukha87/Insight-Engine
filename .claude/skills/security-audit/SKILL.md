---
name: security-audit
description: Scan the codebase for hardcoded secrets, SQL injection, XSS, and other OWASP vulnerabilities
---

# Security Audit

Scan the entire codebase for security vulnerabilities. Run ALL of these checks:

## 1. Hardcoded Secrets
Search for hardcoded passwords, API keys, secrets, and tokens in ALL Python files (project-wide, excluding .venv):
```bash
grep -rn --include="*.py" --exclude-dir=".venv" --exclude-dir=".airflow" -iE "(password|secret_key|api_key|private_key)\s*[=:]\s*[\"'][^\"']{8,}" .
```

Also search for hardcoded defaults inside `os.getenv()` calls — e.g. `os.getenv("NEO4J_PASSWORD", "changeme")`:
```bash
grep -rn --include="*.py" --exclude-dir=".venv" --exclude-dir=".airflow" -iE "os\.getenv\s*\(\s*[\"'](password|secret_key|api_key|private_key|secret|token)[^\"']*[\"']\s*,\s*[\"'][^\"']{4,}[\"']\s*\)" .
```

Search TypeScript/TSX files (scoped to src/frontend/src to avoid node_modules):
```bash
grep -rn --include="*.ts" --include="*.tsx" -iE "(password|secret_key|api_key|private_key)\s*[=:]\s*[\"'][^\"']{8,}" src/frontend/src/
```

Also search for known credential patterns in all Python files and frontend source:
```bash
grep -rn --include="*.py" --exclude-dir=".venv" --exclude-dir=".airflow" -E "(AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,})" .
grep -rn --include="*.ts" --include="*.tsx" -E "(AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,})" src/frontend/src/
```

## 2. SQL / Cypher Injection
Search for string interpolation in SQL/Cypher queries:
```bash
grep -rn --include="*.py" -E "f[\"'](SELECT|INSERT|UPDATE|DELETE|MATCH|MERGE|DROP|ALTER)" src/
grep -rn --include="*.py" -E "\.format\(\).*\b(SELECT|INSERT|UPDATE|DELETE)\b" src/
grep -rn --include="*.py" -E "session\.run\(f[\"']" src/
```

## 3. XSS Vulnerabilities
Search for dangerous HTML injection patterns:
```bash
grep -rn --include="*.tsx" --include="*.ts" "dangerouslySetInnerHTML" src/
```

## 4. Dangerous Functions
```bash
grep -rn --include="*.py" -E "\beval\s*\(" src/ | grep -v "literal_eval"
grep -rn --include="*.py" -E "\bexec\s*\(" src/
grep -rn --include="*.py" "pickle\.loads\|pickle\.load" src/
grep -rn --include="*.py" "shell\s*=\s*True" src/
```

## 5. Credential Files
Check that .env is NOT tracked in git:
```bash
git ls-files .env
```
Should return nothing. Also check .gitignore includes `.env`.

## 6. Token Storage
Verify tokens are hashed before storage — search for raw token assignments to DB:
```bash
grep -rn --include="*.py" "access_token\s*=" src/backend/db/ src/backend/auth/
```
Should show hash_token() or SHA-256 operations, never raw values.

## Summary
Present findings in a table:

| Category | Status | Files | Details |
|----------|--------|-------|---------|

Flag anything found as CRITICAL, WARNING, or PASS.

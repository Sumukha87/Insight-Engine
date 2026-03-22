---
name: frontend-lint
description: Run TypeScript type checking and ESLint on the Next.js frontend
---

# Frontend Lint Check

Run all frontend quality checks from the `src/frontend/` directory.

## 1. TypeScript Type Check
```bash
cd /home/sumukha/Insight-Engine/src/frontend && npx tsc --noEmit 2>&1
```
Zero errors = PASS.

## 2. ESLint
```bash
cd /home/sumukha/Insight-Engine/src/frontend && npx next lint 2>&1
```

## 3. Check for Security Issues in Frontend
```bash
grep -rn "dangerouslySetInnerHTML" /home/sumukha/Insight-Engine/src/frontend/src/
grep -rn "localStorage\.\(setItem\|getItem\).*token" /home/sumukha/Insight-Engine/src/frontend/src/
```
Flag localStorage token usage as a WARNING — recommend httpOnly cookies for production.

## 4. Dependency Audit
```bash
cd /home/sumukha/Insight-Engine/src/frontend && npm audit 2>&1 | tail -20
```

## Summary
| Check | Status | Details |
|-------|--------|---------|

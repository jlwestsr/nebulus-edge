# Project AI Insights (Long-Term Memory)

## Purpose
This document serves as the **Long-Term Memory** for AI agents working on **Nebulus Edge**. It captures project-specific behavioral nuances, recurring pitfalls, and architectural decisions that are not strictly "rules" (in `AI_DIRECTIVES.md`) but are critical for maintaining continuity.

## 1. Architectural Patterns

*   **Artifacts**: Always update `task.md` before tool calls when starting a new phase.
*   **Three-service architecture**: Brain (LLM, port 8080), Intelligence (data analytics, port 8081), Body (Open WebUI, port 3000). All PM2-managed services are defined in `infrastructure/pm2_config.json`.
*   **Intelligence service**: FastAPI server at `intelligence/server.py`, started via `python -m intelligence.server`. Uses `intelligence/storage/` for runtime data (databases, vectors, knowledge, feedback, audit) — this directory is gitignored.
*   **Audit logging architecture**:
    - **Middleware + Dependency Injection hybrid**: AuditMiddleware enriches all requests with context (user_id, IP, session_id, request/response SHA-256 hashes) — cannot be bypassed. Routes explicitly log business operations with domain context.
    - **Separate audit databases**: `brain/audit/audit.db` and `intelligence/storage/audit/audit.db` — services are independent with different lifecycles
    - **SHA-256 hashing strategy**: Full request/response bodies hashed for integrity verification without storing sensitive data (except in AUDIT_DEBUG mode)
    - **7-year retention**: Default AUDIT_RETENTION_DAYS=2555 for HIPAA compliance
    - **Performance impact**: <10ms overhead per request (UUID generation, SHA-256, SQLite insert)
    - **Export/verification**: `scripts/audit_export.py` generates signed CSV exports with HMAC-SHA256 for tamper detection

## 2. Recurring Pitfalls
*   **Testing**: Do not assume tests pass; always checking logs.
*   **Dependencies**: Three levels of requirements — `requirements.txt` (shared runtime), `brain/requirements.txt` and `intelligence/requirements.txt` (service-specific, used by their `start_*.sh` scripts), `requirements-dev.txt` (dev tooling: pytest, flake8, black, ansible). Check all before adding new libraries.
*   **pyproject.toml pythonpath**: Must include both `"src"` and `"."` — the latter is required for `intelligence.*` imports to resolve in pytest.
*   **uvicorn reload**: Intelligence server defaults `reload=False` for production (PM2). Set `INTELLIGENCE_RELOAD=true` env var for local dev only. Hardcoding `reload=True` causes issues under PM2.
*   **make down**: Uses `pm2 stop all` to stop all services. If a new PM2 service is added, it will be stopped automatically — no Makefile change needed.

## 3. Workflow Nuances
*   **Verification**: Trust the test runner (`pytest` or `verify.yml`) over your assumptions.
*   **Start scripts**: Both `start_brain.sh` and `start_intelligence.sh` auto-create the venv if missing. They install their own service-specific requirements on each start.
*   **Pre-commit hooks**: The project runs end-of-file-fixer, black, flake8, and pytest as pre-commit hooks. If a commit fails on end-of-file-fixer, re-stage the modified files and create a new commit (do not amend).

# CLAUDE.md - Project Context for Claude Code

## Project Overview
**Nebulus Edge** is a production-grade, edge-deployed AI system consisting of:
- **Brain**: FastAPI server running local LLMs via MLX (`brain/server.py`)
- **Body**: Open WebUI frontend served via Docker (`body/docker-compose.yml`)
- **Infrastructure**: PM2 process management + Ansible automation

## Technical Stack
- **Language**: Python 3.10+
- **LLM Framework**: MLX (Apple Silicon optimized)
- **API**: FastAPI with OpenAI-compatible `/v1/chat/completions` endpoint
- **Frontend**: Open WebUI (Docker)
- **Process Management**: PM2
- **IaC**: Ansible (executed from venv)
- **Testing**: pytest
- **Linting**: flake8, black

## Architecture
```
┌─────────────────┐    ┌─────────────────┐
│   Body (UI)     │───▶│   Brain (LLM)   │
│  Open WebUI     │    │  FastAPI + MLX  │
│  Port 3000      │    │  Port 8080      │
└─────────────────┘    └─────────────────┘
         Docker              PM2
```

**Available Models** (in `brain/server.py`):
- `qwen3-coder-30b` (default) - MoE model, 30B params / 3B active
- `qwen2.5-coder-32b`
- `llama3.1-8b`

## Critical Directives

### 1. Ansible-First Policy
**Any OS-level change MUST use Ansible**, not shell scripts:
- Package installation
- User/service creation
- System configuration
- Run via: `venv/bin/ansible-playbook ansible/<playbook>.yml`

### 2. Git Workflow (Gitflow-lite)
- **Never commit directly to `main` or `develop`**
- Feature branches are **local only** (`feat/`, `fix/`, `docs/`, `chore/`)
- Merge to `develop` locally, then push only `develop`
- Use **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`

### 3. Testing Requirements
- All changes require tests in `tests/`
- Run before completion: `pytest` or `./scripts/run_tests.sh`
- Strict flake8 compliance (zero errors)
- Type hints mandatory for all functions

### 4. Discovery-Driven Development
- Check existing patterns in `src/` before implementing
- Reference `reference_/` directories as ground truth if they exist
- No assumptions based on "general knowledge"

## Project Commands

```bash
# Start the full stack
make up

# Stop everything
make down

# Run Ansible setup
make setup

# Run tests
pytest

# Start brain only (PM2)
pm2 start infrastructure/pm2_config.json

# Start body only (Docker)
./infrastructure/start_body.sh
```

## Key Files & Directories
| Path | Purpose |
|------|---------|
| `brain/server.py` | Main LLM API server |
| `body/docker-compose.yml` | Open WebUI configuration |
| `infrastructure/pm2_config.json` | PM2 process config |
| `ansible/` | Ansible playbooks and roles |
| `docs/AI_INSIGHTS.md` | Long-term memory for agents |
| `docs/features/` | Feature specifications |
| `AI_DIRECTIVES.md` | Strict operational rules |
| `WORKFLOW.md` | Development workflow details |

## Workflow for Features

1. **Discovery**: Read `docs/AI_INSIGHTS.md`, check existing code
2. **Proposal**: Create `implementation_plan.md` and feature spec in `docs/features/`
3. **Implementation**: Branch from `develop`, write code + tests
4. **Delivery**: Verify with pytest, merge to `develop`, update `AI_INSIGHTS.md`

## Long-Term Memory
Update `docs/AI_INSIGHTS.md` when encountering:
- Project-specific nuances
- Recurring pitfalls
- Architectural constraints

## Documentation (Keep In Sync)

Three public-facing documentation surfaces must stay consistent:

1. **README.md** — Primary landing page. SEO-optimized for GitHub search and Google indexing. Contains keyword-rich sections targeting healthcare, legal, finance, and automotive verticals. **Preserve the SEO keyword sections and comparison table when editing.**
2. **GitHub Wiki** — User-facing guides at `https://github.com/jlwestsr/nebulus-edge/wiki`. Cloned locally at `../nebulus-edge.wiki/` (sibling to main repo, SSH remote). Pages: Home, Installation-Guide, Quick-Start, Architecture-Overview, Audit-Logging.
3. **docs/audit_logging.md** — In-repo reference for audit system internals.

**Rules:**
- When a feature ships or behavior changes, update all three locations.
- The wiki repo is separate from the main repo — commit and push it independently (`cd ../nebulus-edge.wiki && git add . && git commit && git push origin master`).
- README changes go through normal develop branch workflow.
- Wiki uses `master` branch (GitHub default for wikis), not `develop`.

## Dependencies
Main: `requirements.txt`
Brain-specific: `brain/requirements.txt` (includes `mlx-lm`)
Dev: `requirements-dev.txt`

# Nebulus Edge

A privacy-first AI appliance for small businesses handling sensitive data. Run powerful local LLMs on Apple Silicon with a turnkey, on-premise solution.

> **Platform:** macOS only (Apple Silicon required)
> **Target Hardware:** Mac mini M4 Pro with 48GB+ unified memory

## Overview

Nebulus Edge is designed for professionals who need AI capabilities but cannot send data to the cloud:
- **Car dealerships** analyzing inventory and sales
- **Medical practices** reviewing patient data (HIPAA-compliant audit logging)
- **Law firms** processing case documents (attorney-client privilege protection)
- **Accountants** examining financial records

**Key Value Proposition:** Customer owns the hardware. Data never leaves the box.

### Compliance Features

- ✅ **HIPAA-Ready Audit Logging**: 7-year retention, tamper-proof exports, SHA-256 integrity verification
- ✅ **PII Detection**: Automatic detection and logging of sensitive data access
- ✅ **User Tracking**: Session-level accountability with IP addresses and timestamps
- ✅ **Signed Exports**: HMAC-SHA256 signatures for compliance reporting

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Body (UI)     │───▶│   Brain (LLM)   │
│  Open WebUI     │    │  FastAPI + MLX  │
│  Port 3000      │    │  Port 8080      │
└─────────────────┘    └─────────────────┘
       Docker                 PM2
```

| Component | Description |
|-----------|-------------|
| **Brain** | FastAPI server running local LLMs via MLX (Apple Silicon optimized) |
| **Body** | Open WebUI frontend served via Docker |
| **Infrastructure** | PM2 process management + Ansible automation |

## Available Models

| Model | Description |
|-------|-------------|
| `qwen3-coder-30b` (default) | MoE model, 30B params / 3B active |
| `qwen2.5-coder-32b` | Full 32B parameter model |
| `llama3.1-8b` | Lightweight 8B model |

## System Requirements

> **This project is designed exclusively for macOS on Apple Silicon.**
> It uses [MLX](https://github.com/ml-explore/mlx), Apple's machine learning framework optimized for Apple Silicon's unified memory architecture.

### Hardware Requirements

| Spec | Minimum | Recommended |
|------|---------|-------------|
| **Chip** | Apple M1 | Apple M4 Pro |
| **Unified Memory** | 24GB | 48GB+ |
| **Storage** | 50GB free | 100GB+ SSD |
| **Form Factor** | Any Mac with Apple Silicon | Mac mini (headless deployment) |

**Memory guidance by model:**
- `llama3.1-8b` (4-bit): ~6GB RAM
- `qwen3-coder-30b` (4-bit): ~18GB RAM
- `qwen2.5-coder-32b` (4-bit): ~20GB RAM

### Software Requirements

- **macOS 14+** (Sonoma or later)
- **Python 3.10+**
- **Docker Desktop** (for Open WebUI)
- **Node.js 18+** (for PM2 process manager)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jlwestsr/nebulus-edge.git
cd nebulus-edge
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r brain/requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 4. Run Ansible Setup

```bash
make setup
# Or manually:
venv/bin/ansible-playbook ansible/setup.yml
```

### 5. Start the Stack

```bash
make up
```

This starts:
- Brain (LLM server) on port 8080
- Body (Open WebUI) on port 3000

## Usage

### Access the UI

Open http://localhost:3000 in your browser.

### API Endpoints

The Brain exposes an OpenAI-compatible API:

```bash
# Health check
curl http://localhost:8080/

# List models
curl http://localhost:8080/v1/models

# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-coder-30b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

## Project Structure

```
nebulus-edge/
├── brain/                  # LLM server (FastAPI + MLX)
│   ├── server.py           # Main API server
│   ├── audit/              # Audit logs (auto-created)
│   └── requirements.txt    # Brain-specific dependencies
├── intelligence/           # Data analytics service
│   ├── server.py           # Intelligence API server
│   ├── api/                # API routes (data, query, knowledge)
│   └── storage/            # Runtime data (databases, vectors, audit logs)
├── body/                   # Open WebUI configuration
│   └── docker-compose.yml  # Docker setup
├── shared/                 # Shared modules
│   ├── middleware/         # Audit middleware
│   ├── config/             # Configuration (audit, etc.)
│   └── audit/              # Audit export utilities
├── infrastructure/         # Deployment configuration
│   ├── pm2_config.json     # PM2 process config
│   ├── start_brain.sh      # Brain startup script
│   └── start_intelligence.sh # Intelligence startup script
├── scripts/                # Utility scripts
│   └── audit_export.py     # Compliance export/verification tool
├── ansible/                # Ansible playbooks and roles
├── docs/                   # Documentation
│   ├── AI_INSIGHTS.md      # Long-term memory for agents
│   ├── audit_logging.md    # Audit system documentation
│   ├── features/           # Feature specifications
│   └── plans/              # Design documents
├── tests/                  # Test suite (211 tests)
│   ├── integration/        # Integration tests
│   └── test_audit_*.py     # Audit logging tests
├── CLAUDE.md               # AI agent project context
├── AI_DIRECTIVES.md        # Operational rules
└── WORKFLOW.md             # Development workflow
```

## Commands

```bash
# Start full stack
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

# Check brain status
pm2 status

# View brain logs
pm2 logs nebulus-brain
```

## Development

### Git Workflow

This project uses Gitflow-lite:
- **Never commit directly to `main` or `develop`**
- Feature branches are local only (`feat/`, `fix/`, `docs/`, `chore/`)
- Merge to `develop` locally, then push only `develop`
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_initial.py
```

### Linting

```bash
# Check code style
flake8

# Format code
black .
```

## Roadmap

### Phase 1: Core Platform ✓
- [x] Brain: Multi-model support with MLX
- [x] Brain: Model warmup for fast first response
- [x] Body: Open WebUI integration
- [x] Intelligence: Multi-source CSV data analysis
- [x] Intelligence: Domain knowledge layer
- [x] Intelligence: Strategic recommendations
- [x] **Audit Logging: HIPAA-compliant audit system with 7-year retention**

### Phase 2: Enterprise Features (Planned)
- [ ] Multi-user authentication and authorization
- [ ] Role-based access control (RBAC)
- [ ] Encrypted data at rest
- [ ] Automated compliance reporting

## Related Projects

| Project | Description |
|---------|-------------|
| **Nebulus Prime** | Linux version (server/datacenter) |
| **Nebulus Gantry** | Custom web UI (Open WebUI fork) |
| **Nebulus Atom** | AI agent system |

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Contributing

1. Create a feature branch from `develop`
2. Make your changes with tests
3. Ensure `pytest` and `flake8` pass
4. Submit a PR to `develop`

For major changes, please open an issue first to discuss what you would like to change.

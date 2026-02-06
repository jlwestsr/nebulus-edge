# Nebulus Edge - HIPAA-Compliant On-Premise AI for Healthcare, Legal & Finance

**Privacy-First Local AI Appliance | No Cloud Required | Your Data Never Leaves Your Device**

Nebulus Edge is a production-grade, HIPAA-compliant AI system designed for professionals handling sensitive data. Run powerful large language models (LLMs) locally on Apple Silicon with complete data privacy and regulatory compliance.

> **Platform:** macOS on Apple Silicon (M1, M2, M3, M4, M4 Pro)
> **Ideal Hardware:** Mac mini M4 Pro with 48GB+ unified memory
> **Compliance:** HIPAA-ready audit logging | 7-year retention | BAA-compatible
> **Processing:** 100% on-device | Zero cloud connectivity | Air-gap capable

## Why Nebulus Edge?

### For Healthcare & Medical Practices 🏥

**HIPAA-Compliant AI for Patient Data**
- ✅ 7-year audit retention (HIPAA §164.312(b))
- ✅ Automatic PII/PHI detection and logging
- ✅ Tamper-proof audit exports for compliance audits
- ✅ Business Associate Agreement (BAA) ready
- ✅ Zero cloud exposure - eliminates breach risk
- ✅ Patient data never leaves your office

Perfect for: Medical practices, hospitals, healthcare providers, mental health professionals, physical therapy clinics.

### For Legal Firms & Attorneys ⚖️

**Attorney-Client Privilege Protected AI**
- ✅ Complete data sovereignty - you own the hardware
- ✅ Session-level audit trails for client work
- ✅ Document analysis without cloud uploads
- ✅ Case research with local AI models
- ✅ Ethical compliance for confidential communications
- ✅ Air-gap deployment option for maximum security

Perfect for: Law firms, corporate legal departments, solo practitioners, legal research teams.

### For Accounting & Financial Services 💼

**Secure AI for Sensitive Financial Data**
- ✅ Client confidentiality maintained
- ✅ Tax document analysis on-premise
- ✅ Financial data never transmitted to cloud
- ✅ Audit trails for regulatory compliance
- ✅ Multi-year data retention
- ✅ SOC 2 / GLBA compliance support

Perfect for: CPA firms, accounting practices, financial advisors, tax preparation services.

### For Automotive Dealerships 🚗

**Privacy-First AI for Customer & Sales Data**
- ✅ Customer PII protection
- ✅ Inventory analysis and optimization
- ✅ Sales forecasting with local AI
- ✅ No customer data shared with third parties
- ✅ GDPR/CCPA compliance ready

Perfect for: Car dealerships, automotive groups, used car lots, fleet management.

### 🔒 Enterprise-Grade Security & Compliance

**HIPAA-Compliant Audit System**
- 7-year audit log retention (meets HIPAA §164.312(b) requirements)
- Automatic PII/PHI detection (email, SSN, credit cards, phone numbers)
- Tamper-proof CSV exports with HMAC-SHA256 signatures
- SHA-256 integrity verification prevents data modification
- User, session, and IP tracking for full accountability
- Ready for Business Associate Agreements (BAA)

**Privacy-First Architecture**
- **100% local processing** - no data transmission to cloud
- **Air-gap deployment capable** - can run completely offline
- **On-premise LLM inference** - models run on your Mac mini
- **Customer-owned hardware** - complete data sovereignty
- **Zero vendor lock-in** - open source, MIT licensed

**Compliance Standards Supported**
- ✅ HIPAA (Health Insurance Portability and Accountability Act)
- ✅ HITECH (Health Information Technology for Economic and Clinical Health Act)
- ✅ Attorney-client privilege compliance
- ✅ GDPR (General Data Protection Regulation) ready
- ✅ CCPA (California Consumer Privacy Act) ready
- ✅ SOC 2 audit trail support
- ✅ GLBA (Gramm-Leach-Bliley Act) support

**[📖 Read Full Audit Logging Documentation](https://github.com/jlwestsr/nebulus-edge/wiki/Audit-Logging)**

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

## 🎯 Key Features

### Local LLM Inference (No Cloud Required)
- **Qwen3-Coder-30B** (30 billion parameter AI model)
- **Qwen2.5-Coder-32B** (32 billion parameter model)
- **Llama 3.1 8B** (lightweight 8 billion parameter model)
- **MLX-optimized** for Apple Silicon's unified memory
- **OpenAI-compatible API** for easy integration

### Intelligent Data Analytics
- **Multi-source CSV data ingestion** with automatic schema detection
- **Natural language queries** - ask questions in plain English
- **Semantic search** powered by ChromaDB vector database
- **SQL query execution** with safety controls
- **PII detection** for GDPR/CCPA/HIPAA compliance
- **Domain knowledge integration** for industry-specific insights

### Production-Ready Deployment
- **PM2 process management** for reliability
- **Docker-based UI** (Open WebUI)
- **Ansible automation** for provisioning
- **Health monitoring** and auto-restart
- **211 automated tests** for quality assurance

### Performance & Scalability
- **2-10 second inference** for typical queries
- **<10ms audit overhead** per request
- **Handles 5-10 concurrent users** per appliance
- **Processes up to 1GB CSV files** in memory
- **Scales to 1M+ vector embeddings**

## 💻 System Requirements

> **This is an on-premise AI solution designed exclusively for macOS on Apple Silicon.**
> It uses [MLX](https://github.com/ml-explore/mlx), Apple's machine learning framework optimized for Apple Silicon's unified memory architecture, to run large language models locally.

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

## 📚 Documentation & Resources

**Complete guides available in our [GitHub Wiki](https://github.com/jlwestsr/nebulus-edge/wiki)**:

- [**Installation Guide**](https://github.com/jlwestsr/nebulus-edge/wiki/Installation-Guide) - Step-by-step Mac mini M4 Pro setup
- [**Quick Start**](https://github.com/jlwestsr/nebulus-edge/wiki/Quick-Start) - Get running in 15 minutes
- [**Audit Logging**](https://github.com/jlwestsr/nebulus-edge/wiki/Audit-Logging) - HIPAA compliance setup
- [**Architecture Overview**](https://github.com/jlwestsr/nebulus-edge/wiki/Architecture-Overview) - System design deep-dive
- [**API Reference**](https://github.com/jlwestsr/nebulus-edge/wiki) - Complete API documentation
- [**HIPAA Compliance**](https://github.com/jlwestsr/nebulus-edge/wiki/HIPAA-Compliance) - Healthcare regulations guide

## 🚀 Quick Installation

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

## 🔍 Search Keywords

**Find this project by searching for:**
- HIPAA compliant AI
- On-premise LLM for healthcare
- Local AI for medical practices
- Private LLM for law firms
- HIPAA AI appliance
- On-device large language model
- Medical practice AI solution
- Attorney-client privilege AI
- Apple Silicon AI server
- Mac mini AI appliance
- Local ChatGPT alternative
- Private AI for small business
- GDPR compliant AI
- Air-gap AI deployment
- Healthcare AI with audit logging
- Medical data AI analysis
- Local LLM inference Mac
- Privacy-first artificial intelligence

## 🏆 Why Choose Nebulus Edge Over Cloud AI?

| Feature | Nebulus Edge | Cloud AI (ChatGPT, etc.) |
|---------|--------------|--------------------------|
| **Data Privacy** | ✅ 100% local | ❌ Transmitted to cloud |
| **HIPAA Compliance** | ✅ Built-in audit logging | ⚠️ Requires BAA, limitations apply |
| **Cost** | One-time hardware | Ongoing per-token fees |
| **Latency** | <10 seconds | Variable (network dependent) |
| **Internet Required** | ❌ Can run air-gapped | ✅ Always required |
| **Data Sovereignty** | ✅ Customer owns everything | ❌ Vendor controls data |
| **Audit Trails** | ✅ 7-year retention | ⚠️ Limited, vendor-controlled |
| **PHI/PII Protection** | ✅ Never leaves device | ❌ Transmitted to third party |
| **Customization** | ✅ Full control | ⚠️ Limited |
| **Vendor Lock-in** | ❌ Open source | ⚠️ Proprietary |

## 🎓 Learning Resources

### For Healthcare Professionals
- Understanding HIPAA requirements for AI systems
- How audit logging protects patient privacy
- Setting up BAA-compliant AI infrastructure
- Best practices for PHI protection

### For Legal Professionals
- Attorney-client privilege in AI systems
- Ethical compliance for legal tech
- Document analysis without cloud exposure
- Audit trails for client work

### For IT Administrators
- Deploying on-premise AI appliances
- Mac mini M4 Pro optimization
- PM2 process management
- Audit log management and exports

## 🌟 Use Cases

### Medical Practice Examples
- **Chart Review**: Analyze patient charts with local AI
- **Medical Coding**: Assist with ICD-10 coding
- **Research**: Literature review without PHI exposure
- **Documentation**: Clinical note summarization

### Legal Firm Examples
- **Contract Analysis**: Review agreements locally
- **Case Research**: Legal research without cloud
- **Discovery**: Document review on-premise
- **Brief Writing**: AI-assisted legal writing

### Accounting Examples
- **Tax Preparation**: Analyze returns locally
- **Financial Analysis**: Client data analytics
- **Audit Support**: Documentation review
- **Reporting**: Automated report generation

## 📞 Support & Community

- **Documentation**: [GitHub Wiki](https://github.com/jlwestsr/nebulus-edge/wiki)
- **Issues**: [GitHub Issues](https://github.com/jlwestsr/nebulus-edge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jlwestsr/nebulus-edge/discussions)
- **Security**: See SECURITY.md for vulnerability reporting

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

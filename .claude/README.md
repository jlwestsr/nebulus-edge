# Claude Code Configuration — nebulus-edge

**Project Type:** Python CLI + Backend Services
**Platform:** macOS (Bare-metal MLX, Apple Silicon)
**Configuration Date:** 2026-02-06

---

## Overview

Per-project Claude Code plugin configuration for Nebulus Edge, the macOS deployment platform with bare-metal MLX inference and PM2 orchestration.

## Enabled Plugins

### High Priority

- ✅ **Pyright LSP** — Type checking for CLI and service code
- ✅ **Serena** — Navigate codebase (CLI, adapters, services)
- ✅ **Superpowers** — TDD and debugging workflows

### Medium Priority

- ✅ **Context7** — Live docs for MLX, PM2, ChromaDB
- ✅ **PR Review Toolkit** — Code quality checks
- ✅ **Commit Commands** — Git workflow automation
- ✅ **Feature Dev** — Feature development workflows
- ✅ **GitHub** — Release management and wiki publishing

## Disabled Plugins

- ❌ **TypeScript LSP** — No TypeScript
- ❌ **Playwright** — No UI testing
- ❌ **Supabase** — Not using Supabase
- ❌ **Ralph Loop** — No automation loops

## LSP Configuration

### Pyright

Configuration: `pyrightconfig.json` (project root)

**Settings:**

- Type checking: basic
- Python version: 3.10+
- Include: `nebulus_edge/`, `intelligence/`
- Exclude: `__pycache__`, `.pytest_cache`, `data/`, `models/`
- Virtual environment: `./.venv`

## Architecture

Edge follows the shared core + platform adapter pattern:

- Installs `nebulus-core` as dependency
- Registers `EdgeAdapter` via entry points
- Provides MLX-based inference
- Manages PM2 process orchestration

## Testing

Run tests via pytest:

```bash
pytest tests/ -v
```

## Workflow

This project follows the develop→main git workflow:

1. Branch off `develop` for new work
2. Merge features back to `develop` with `--no-ff`
3. Release from `develop` to `main` with version tags

## Why These Plugins?

**Pyright LSP** — Platform adapter code interfaces with nebulus-core. Type checking prevents integration bugs.

**Serena** — Codebase includes CLI, adapters, PM2 configs, and MLX integration. Semantic navigation essential.

**Context7** — MLX (Apple's ML framework) has rapid development. Live docs keep us current on API changes.

**GitHub** — Edge has releases and wiki documentation. GitHub integration streamlines publishing.

## Maintenance

Update this configuration when:

- Adding new services or components
- Performance issues (disable low-value plugins)
- New Claude Code plugins that benefit deployment projects

---

*Part of the West AI Labs plugin strategy. See `../docs/claude-code-plugin-strategy.md` for ecosystem-wide strategy.*

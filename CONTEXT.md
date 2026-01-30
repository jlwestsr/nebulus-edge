# Project Context & Coding Standards

> **[IMPORTANCE: CRITICAL] AI AGENT DIRECTIVE**:
> You MUST read and adhere to [AI_DIRECTIVES.md](AI_DIRECTIVES.md) at the start of every session. It contains strict operational guardrails, "Ansible-First" policies, and Git branching rules that supersede general instructions.

## Project Overview
This is a production-grade AI engineering project. 

## Coding Standards
1. **Unit Tests**: ALL changes must have accompanying unit tests in the `tests/` directory.
2. **Modular Code**: Do not put business logic in notebooks. Move logic to `src/` modules.
3. **Type Hinting**: Use Python type hints for all function definitions.
4. **Documentation**: All public functions must have docstrings (Google style).

## Git Workflow
1. We use Git Flow.
2. Direct commits to `main` are forbidden. 
3. Work on feature branches off `develop`.
4. Ensure `git init` and `.gitignore` are respected.

## File Structure
- `data/`: Contains raw and processed data. **Ignored by git** to prevent leaking sensitive information.
- `docs/`: Project documentation, including feature specs (in `features/`) and architectural decisions.
- `models/`: Binary model files and weights. **Ignored by git**.
- `notebooks/`: Jupyter notebooks for experimentation and analysis. Logic MUST be moved to `src/` before production.
- `AI_DIRECTIVES.md`: AI compliance and behavior rules.
- `src/`: The core source code of the project. Organized by feature or module.
- `tests/`: Unit tests mirroring the `src/` structure.
- `.github/`: CI/CD pipelines and GitHub Actions workflows.
# AI Directives for ai_project

These rules are critical for any AI agent "loading" this project. They encode the architectural standards and best practices for developing ai_project.

## 1. Discovery-Driven Development
- **Ground Truth**: Before proposing any changes, check existing architecture in `src/`.
- **Reference Awareness**: If a `reference_` directory exists, use it as the "Ground Truth".
- **No Assumptions**: Do not implement features based on "general knowledge"; implement them based on the existing codebase patterns.

## 2. Architecture Standards


## 3. Testing & Quality Assurance
- **Mandatory Unit Tests**: ALL changes must be verified in `tests/`.

- **Pre-Commit Verification**: Run `./scripts/run_tests.sh` (or `pytest`) before marking any task as complete.

- **Strict Linting**:
    -   **Python**: `flake8` (Zero errors).
    -   **Type Hints**: Mandatory for all new functions.

## 4. Development Workflow
- **Conventional Commits**: Use `feat:`, `fix:`, `docs:`, or `chore:` prefixes.
- **Git Tracking**:
    -   **NO DIRECT WORK ON MAIN/MASTER**.
    -   **Strict Local Branch Policy**: `feat`, `fix`, `docs`, and `chore` branches are **LOCAL ONLY**.
    -   Always merge `develop` into your feature branch before requesting a merge back.

## 5. Agentic Artifact Protocol
- **Task Tracking**: For complex tasks, maintain a `task.md` artifact to track progress.
- **Planning**: Before "Doing the Work" (Step 2 of Feature Workflow), create an `implementation_plan.md` for user approval.
- **Walkthrough**: Upon completion of significant features, create `walkthrough.md`.

## 6. Project Long-Term Memory
- **Mandate**: You are explicitly required to update `docs/AI_INSIGHTS.md` whenever you encounter a project-specific nuance, recurring pitfall, or architectural constraint.
- **Trigger**: If you find yourself thinking "I should remember this for next time" or "This was unexpected," you MUST document it in `docs/AI_INSIGHTS.md`.
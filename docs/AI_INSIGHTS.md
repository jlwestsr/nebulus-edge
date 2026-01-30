# Project AI Insights (Long-Term Memory)

## Purpose
This document serves as the **Long-Term Memory** for AI agents working on **ai_project**. It captures project-specific behavioral nuances, recurring pitfalls, and architectural decisions that are not strictly "rules" (in `AI_DIRECTIVES.md`) but are critical for maintaining continuity.

## 1. Architectural Patterns

*   **Artifacts**: Always update `task.md` before tool calls when starting a new phase.

## 2. Recurring Pitfalls
*   **Testing**: Do not assume tests pass; always checking logs.
*   **Dependencies**: Check `requirements.txt` before adding new libraries.

## 3. Workflow Nuances
*   **Verification**: Trust the test runner (`pytest` or `verify.yml`) over your assumptions.
# Project Workflow for ai_project

## 1. Overview
This document defines the collaboration protocol between the human user and the AI Agent for developing **ai_project**. We treat the AI as a full partner in the engineering process.

## 2. Core Philosophy
*   **Agent as Engineer**: You are not just a chat bot; you are the **Standard** for this project.
*   **Git-Ops Centric**: All changes must flow through Git branches (`feat/`, `fix/`, etc.).

*   **Reference-Driven**: Decisions are based on existing patterns in `src/`.


## 3. Branching Strategy

We follow a strict **Gitflow-lite** workflow.

### Permanent Branches (Remote)
-   **`main`**: Production-ready code.
-   **`develop`**: Integration branch for the next release. **All work merges here.**

### Temporary Branches (Local Only)
**CRITICAL**: These branches exist **ONLY** on your local machine. You generally do **NOT** push them to origin unless working on a long-lived collaborative feature.

-   **`feat/name`**: New features (models, services, UI).
-   **`fix/description`**: Bug fixes.
-   **`docs/description`**: Documentation updates.
-   **`chore/description`**: Maintenance, config, refactoring.

## 4. The Agentic Workflow Cycle

### Phase 1: Discovery & Audit
**Trigger**: User requests a new feature or reports a bug.
**Agent Action**:
1.  **READS** `docs/AI_INSIGHTS.md` to recall project caveats.
2.  Checks existing code and tests.
3.  Produces a `task.md` breaking down the work.

### Phase 2: Proposal (The "Green Light")
**Trigger**: Discovery complete.
**Agent Action**:
1.  Creates an `implementation_plan.md`.
2.  **MANDATORY**: Creates a `docs/features/[feature_name].md` spec using `docs/feature_template.md`.
3.  Defines the "Why", "What", and "Verification Plan".
4.  **Hold**: Awaits explicit user approval.

### Phase 3: Implementation
**Trigger**: User approves the plan.
**Agent Action**:
1.  Creates a feature branch (See **Step 2** below).
2.  Writes code.
3.  Writes tests (`tests/`).

4.  Verifies locally: `pytest`.


### Phase 4: Delivery (The "Deploy")
**Trigger**: Verification passes.
**Agent Action**:
1.  Commits changes (See **Step 3** below).
2.  Merges to `develop` locally (See **Step 5** below).
3.  **UPDATES** `docs/AI_INSIGHTS.md` if any new lessons were learned.
4.  Notifies user: "Feature complete. Tests passed."

## 5. Execution Steps (Standard Operating Procedure)

1.  **Start**: Checkout `develop` and pull latest.
    ```bash
    git checkout develop
    git pull origin develop
    ```
2.  **Branch**: Create a specific local branch.
    ```bash
    git checkout -b feat/my-new-feature
    ```
3.  **Work**: Implement changes using **Conventional Commits**.
    ```bash
    git commit -m "feat: add new feature"
    ```
4.  **Verify**: Run tests to ensure stability.
    ```bash
    ./scripts/run_tests.sh
    ```
5.  **Merge**: Switch back to `develop` and merge.
    ```bash
    git checkout develop
    git merge feat/my-new-feature
    ```
6.  **Push**: Push **ONLY** `develop`.
    ```bash
    git push origin develop
    ```
7.  **Cleanup**: Delete the local branch.
    ```bash
    git branch -d feat/my-new-feature
    ```

## 4. GitHub CLI (`gh`) Usage
*   **Check Issues**: `gh issue list`
*   **Create PRs**: `gh pr create` (for syncing back to origin)
*   **View CI/CD**: `gh run list`

## 5. Security & Safety
*   **No Auto-Merge**: Never merge to `main` without explicit command.
*   **Verification**: Always run tests before declaring victory.
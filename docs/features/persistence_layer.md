# Feature: Persistence Layer (PM2 & Makefile)

## 1. Overview
**Branch**: `feat/persistence-layer`

This feature implements robust process management for the "Brain" layer using PM2 and standardizes build/run commands using a Makefile. This simplifies the developer workflow and ensures the Python backend runs reliably.

## 2. Requirements
- [ ] Install `node` and `pm2` via Ansible (using local venv for execution).
- [ ] Configure PM2 to run the Brain layer (`nebulus-brain`).
- [ ] Create `Makefile` with `install`, `up`, and `down` targets.
- [ ] `make up` must start both Brain (PM2) and Body (Docker).
- [ ] `make down` must stop both.

## 3. Technical Implementation
- **Modules**:
  - `infrastructure/pm2_config.json` (New)
  - `Makefile` (New)
  - `requirements-dev.txt` (Update: add ansible)
  - `ansible/roles/persistence` (New)
  - `ansible/setup_nebulus.yml` (Update)
- **Dependencies**: Node.js, PM2, Ansible (venv verified)
- **Data**: PM2 logs (auto-managed).

## 4. Verification Plan
**Automated Tests**:
- [ ] Ansible Playbook (Venv): `venv/bin/ansible-playbook ansible/setup_nebulus.yml`
- [ ] Process Check: `pm2 status | grep nebulus-brain`

**Manual Verification**:
- [ ] Run `make up` - verify endpoints.
- [ ] Run `make down` - verify shutdown.
- [ ] Verify Ansible installs PM2 globally.

## 5. Workflow Checklist
Follow the AI Behavior strict workflow:
- [ ] **Branch**: Created `feat/persistence-layer` branch?
- [ ] **Work**: Implemented changes?
- [ ] **Test**: All tests pass?
- [ ] **Doc**: Updated `README.md` and `walkthrough.md`?
- [ ] **Data**: `git add .`, `git commit`, `git push`?

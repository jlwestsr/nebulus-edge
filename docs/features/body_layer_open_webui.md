# Feature: Body Layer - Open WebUI

## 1. Overview
**Branch**: `feat/body-layer`

This feature implements the "Body" layer of the Nebulus Edge appliance using Open WebUI running in Docker. It provides a user-friendly chat interface for the local MLX "Brain" layer.

## 2. Requirements
- [ ] Provide Open WebUI interface via Docker.
- [ ] Accessible at `http://localhost:3000`.
- [ ] Connect to local Brain layer via `host-gateway`.
- [ ] Ensure compatibility with Brain API (OpenAI format).
- [ ] Automate deployment via Ansible.

## 3. Technical Implementation
- **Modules**:
  - `body/docker-compose.yml` (New)
  - `infrastructure/start_body.sh` (New)
  - `brain/server.py` (Refactor for `/v1/chat/completions`)
  - `ansible/roles/body` (New)
  - `ansible/setup_nebulus.yml` (New playbook)
- **Dependencies**: Docker (System), `pydantic` (Python)
- **Data**: Docker volumes for Open WebUI persistence.

## 4. Verification Plan
**Automated Tests**:
- [ ] Ansible verification: `ansible-playbook ansible/setup_nebulus.yml`
- [ ] Container check: `docker ps | grep open-webui`

**Manual Verification**:
- [ ] Run `infrastructure/start_body.sh`
- [ ] Browse `http://localhost:3000`
- [ ] Create simple chat completion "Hello World"

## 5. Workflow Checklist
Follow the AI Behavior strict workflow:
- [ ] **Branch**: Created `feat/body-layer` branch?
- [ ] **Work**: Implemented changes?
- [ ] **Test**: All tests pass (`pytest` / connection check)?
- [ ] **Doc**: Updated `README.md` and `walkthrough.md`?
- [ ] **Data**: `git add .`, `git commit`, `git push`?

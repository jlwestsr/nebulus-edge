SHELL := /bin/bash
VENV_PYTHON = venv/bin/python
VENV_PIP = venv/bin/pip
VENV_ANSIBLE = venv/bin/ansible-playbook

.PHONY: install up down setup

install:
	@echo "Installing dependencies..."
	@./infrastructure/start_brain.sh --dry-run
	@echo "Dependencies installed."

setup:
	@echo "Running Ansible Setup..."
	@$(VENV_PIP) install ansible
	@$(VENV_ANSIBLE) ansible/setup_nebulus.yml

up:
	@echo "Starting Nebulus Edge..."
	@echo "Starting Brain (PM2)..."
	@pm2 start infrastructure/pm2_config.json
	@echo "Starting Body (Docker)..."
	@./infrastructure/start_body.sh

down:
	@echo "Stopping Nebulus Edge..."
	@echo "Stopping Brain..."
	@pm2 stop nebulus-brain || true
	@echo "Stopping Body..."
	@cd body && docker compose down

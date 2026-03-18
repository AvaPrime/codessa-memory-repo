#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp -n .env.example .env || true
echo "Bootstrap complete. Edit .env, then run: uvicorn codessa_memory.api.main:app --reload"

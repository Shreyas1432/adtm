#!/usr/bin/env bash
# ADTM dev / cloud bootstrap: create a venv, install test deps, run the suite.
# Use as the setup command for a Claude Code cloud environment, or run locally.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-dev.txt
pytest -q

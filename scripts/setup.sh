#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}
VENV_DIR=${VENV_DIR:-.venv}

command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "Python not found: $PYTHON_BIN"; exit 1; }

echo "Welcome to the Doxibox setup (macOS/Linux)."
read -rp "Virtualenv directory [${VENV_DIR}]: " VENV_DIR_INPUT
VENV_DIR=${VENV_DIR_INPUT:-$VENV_DIR}

echo "Select extras to install (comma-separated). Options: dev,audio,tts,asr,llm,modal,full"
read -rp "Extras [dev]: " EXTRAS_INPUT
EXTRAS=${EXTRAS_INPUT:-dev}

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -e ".[${EXTRAS}]"

cat <<INFO
Doxibox environment ready.
- To activate: source ${VENV_DIR}/bin/activate
- To run tests: pytest

Optional Modal setup (for remote LLM execution):
  pip install modal
  python3 -m modal setup
INFO

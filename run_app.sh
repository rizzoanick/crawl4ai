#!/usr/bin/env bash
set -e
DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Activate virtual environment if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
elif [ -d "venv" ]; then
  source venv/bin/activate
fi

export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
exec streamlit run app.py

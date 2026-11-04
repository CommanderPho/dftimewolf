#!/bin/bash
set -e

PYTHONPATH="/app"

# Run the container the default way
if [[ "$1" =~ 'envshell' ]]; then
    source /app/.venv/bin/activate
    exec bash
fi

if [[ "$1" =~ 'tests' ]]; then
    uv run python -m unittest discover -s tests -p '*.py'
fi

# Run a custom command on container start
exec "$@"

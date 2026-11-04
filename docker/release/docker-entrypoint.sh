#!/bin/bash
set -e

PYTHONPATH="/app"

# Pass all args to dftimewolf
if [[ "$1" =~ 'dftimewolf' ]]; then
    uv run dftimewolf "${@:2}"
else
    # Run a custom command on container start
    exec "$@"
fi

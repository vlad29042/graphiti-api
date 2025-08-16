#!/bin/bash
set -e

# Install the local graphiti fork if it exists
if [ -d "/graphiti-fork" ]; then
    echo "Installing local graphiti fork..."
    pip install -e /graphiti-fork
fi

# Execute the original command
exec "$@"
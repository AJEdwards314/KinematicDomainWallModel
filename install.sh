#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# Define 'modules' directory and path for the symlink
MODULES_DIR="$SCRIPT_DIR/src"

# Step 3: Look for a '.venv' directory in the parent directory or its parents
VENV_DIR=""
CURRENT_DIR="$(pwd)"
MAX_DEPTH=10
COUNTER=0

while [ "$CURRENT_DIR" != "/" ]; do
    COUNTER=$((COUNTER + 1))
    if [ $COUNTER -gt $MAX_DEPTH ]; then
        echo "Reached the maximum search depth of $MAX_DEPTH. '.venv' not found." >&2
        exit 1
    fi

    if [ -d "$CURRENT_DIR/.venv" ]; then
        VENV_DIR="$CURRENT_DIR/.venv"
        break
    fi
    CURRENT_DIR=$(dirname "$CURRENT_DIR")  # Move to the parent directory
done

if [ -z "$VENV_DIR" ]; then
    echo "'.venv' directory not found. Exiting." >&2
    exit 1
else
    echo "Found '.venv' directory at: $VENV_DIR"
fi

# Step 4: Create or update the 'nmrc.pth' file in '.venv/Lib/site-packages'
SITE_PACKAGES_PATH="$VENV_DIR/Lib/site-packages"
if [ ! -d "$SITE_PACKAGES_PATH" ]; then
    echo "'Lib/site-packages' not found in '.venv'. Exiting." >&2
    exit 1
fi

PTH_FILE_PATH="$SITE_PACKAGES_PATH/kdw.pth"
echo "$MODULES_DIR" > "$PTH_FILE_PATH"
echo "'kdw.pth' file created at: $PTH_FILE_PATH with content pointing to: $MODULES_DIR"

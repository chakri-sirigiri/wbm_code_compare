#!/bin/bash

# Example script to run the webMethods Branch Comparator
# This uses the webMethods Sample Project (now IBM webMethods)

# execute uv sync
uv sync

REPO_URL="https://github.com/softwareag/webmethods-sample-project-layout.git"
BASE_BRANCH="master"
HEAD_BRANCH="develop" # In a real scenario, this would be your feature branch

echo "Testing with IBM/SoftwareAG sample repository..."
echo "Repo: $REPO_URL"
echo "Base: $BASE_BRANCH"
echo "Head: $HEAD_BRANCH"
echo "------------------------------------------------"

# Method 1: Run as a module (Recommended)
.venv/bin/python -m src.main \
    --scenario 1 \
    --repo "$REPO_URL" \
    --base "$BASE_BRANCH" \
    --head "$HEAD_BRANCH"

# Method 2: Run with PYTHONPATH (If you prefer running the file directly)
# PYTHONPATH=. uv run python3 src/main.py \
#     --repo "$REPO_URL" \
#     --base "$BASE_BRANCH" \
#     --head "$HEAD_BRANCH"

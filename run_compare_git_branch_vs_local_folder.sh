#!/bin/bash

# run_compare_git_branch_vs_local_folder.sh
# This script demonstrates comparing a remote branch vs a local folder.

# execute uv sync to install dependencies
uv sync

REPO_URL="https://github.com/softwareag/webmethods-sample-project-layout.git"
BRANCH="master"

# Create a dummy local structure for demonstration if it doesn't exist
LOCAL_PATH="./tmp/demo_local"
mkdir -p "$LOCAL_PATH/assets/IS/Packages/DemoPkg/ns/DemoPkg/MainFlows/processOrder"
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?><flow></flow>" > "$LOCAL_PATH/assets/IS/Packages/DemoPkg/ns/DemoPkg/MainFlows/processOrder/flow.xml"
echo "v3" > "$LOCAL_PATH/assets/IS/Packages/DemoPkg/manifest.v3"

mkdir -p "$LOCAL_PATH/assets/IS/Properties"
echo "DV properties" > "$LOCAL_PATH/assets/IS/Properties/DV_Demo.xml"

echo "Running Branch in Repo vs Local Folder comparison..."
.venv/bin/python -m src.main \
    --scenario 2 \
    --repo "$REPO_URL" \
    --base "$BRANCH" \
    --local-pkgs "$LOCAL_PATH" \
    --local-props "$LOCAL_PATH"

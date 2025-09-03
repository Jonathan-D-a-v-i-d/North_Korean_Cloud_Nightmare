#!/usr/bin/env bash
set -euo pipefail

# Friendly first-run messages
echo
echo "==============================================="
echo " Codespace ready!"
echo " • Run: aws configure  (paste your keys)"
echo " • Set Pulumi token:   export PULUMI_ACCESS_TOKEN=...  (or Codespaces secret)"
echo " • Check versions:"
aws --version || true
pulumi version || true
python --version || true
echo "==============================================="
echo

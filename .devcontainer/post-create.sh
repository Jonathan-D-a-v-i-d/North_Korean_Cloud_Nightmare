#!/usr/bin/env bash
set -euo pipefail

echo "[*] Running post-create tasks..."

# Ensure Python dependencies are always fresh
if [ -f requirements.txt ]; then
  echo "[*] Installing/updating Python dependencies..."
  pip install --no-cache-dir -r requirements.txt
fi

# (Optional) Pulumi plugins your project needs
# pulumi plugin install resource aws v6.0.0 || true

echo "[*] Post-create complete!"

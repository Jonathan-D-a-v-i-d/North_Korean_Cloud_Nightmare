#!/usr/bin/env bash
set -euo pipefail

# Re-run Python deps in case requirements changed after build
if [ -f requirements.txt ]; then
  pip install --no-cache-dir -r requirements.txt
fi

# (Optional) Install Pulumi plugins/providers your code needs so first run is smooth
# pulumi plugin install resource aws v6.0.0 || true

echo "Post-create complete."

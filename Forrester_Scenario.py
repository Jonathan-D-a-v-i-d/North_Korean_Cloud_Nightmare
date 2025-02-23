import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation


def forrester_scenario_execute():
    """🚀 Execute Pulumi Deployment for the Forrester 2025 Attack Scenario"""
    
    print("-" * 30)
    print(colored("Executing Forrester 2025 Scenario: Compromise DevOps User, takeover, priv escalation, perform ransomware on S3 & DynamoDB", color="red"))
    loading_animation()
    print("-" * 30)

    print(colored("Rolling out Infrastructure via Pulumi", color="red"))
    loading_animation()
    print("-" * 30)

    file_path = ".Infra/forrester-2025-output.json"
    
    # ✅ Ensure Previous Pulumi Output is Removed
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"📂 Previous Pulumi output file '{file_path}' found and deleted.")
    else:
        print(f"📂 Pulumi output file '{file_path}' not found, proceeding...")

    # ✅ Execute Pulumi Deployment
    subprocess.call("cd ./Infra/ && pulumi up -s dev -y", shell=True)
    
    # ✅ Capture Pulumi Stack Output
    subprocess.call("cd ./Infra/ && pulumi stack -s dev output --json > forrester-2025-output.json", shell=True)
    print("📂 Pulumi output saved inside Infra/:forrester-2025-output.json")


def forrester_scenario_validate_rollout():
    """🔍 Validate that Pulumi successfully deployed all resources"""
    
    Functions.wait_for_output_file()
    Functions.validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="Infra/forrester-2025-output.json")


def forrester_scenario_validate_data():
    """🔍 Validate that Pulumi-created data exists in S3 and DynamoDB"""

    print("\n🚀 Running Post-Deployment Validation Checks...")

    # ✅ Ensure Pulumi Stack Output is Up to Date
    subprocess.run("cd Infra/ && pulumi stack -s dev output --json > forrester-2025-output.json", shell=True)

    # ✅ Load Pulumi Outputs
    with open("Infra/forrester-2025-output.json", "r") as file:
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




# ✅ Run Deployment
forrester_scenario_execute()
forrester_scenario_validate_rollout()
forrester_scenario_validate_data()



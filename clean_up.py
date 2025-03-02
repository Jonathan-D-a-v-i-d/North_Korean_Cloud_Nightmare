import boto3
import json
import subprocess
import time
from datetime import datetime, timezone
import os
import shutil
import sys


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
        print("✅ Python cache cleared.")


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
    s3_exfil = "/workspaces/Pulumi/s3_Exfiltration"
    if os.path.exists(s3_exfil):
        print(f"\nDeleting {s3_exfil} and all its contents...")
        shutil.rmtree(s3_exfil)
        print("s3_Exfiltration folder deleted successfully!")
    else:
        print("No existing s3_Exfiltration folder found. Nothing to delete.")



def delete_dynamo_exfil_folder():
    """Delete DynamoDB_Exfiltration folder"""
    dynamo_exfil = "/workspaces/Pulumi/DynamoDB_Exfiltration"
    if os.path.exists(dynamo_exfil):
        print(f"\nDeleting {dynamo_exfil} and all its contents...")
        shutil.rmtree(dynamo_exfil)
        print("DynamoDB_Exfiltration deleted successfully!")
    else:
        print("No existing DynamoDB_Exfiltration found. Nothing to delete.")



def full_cleanup():
    """ 
         Deploys cleanup opposote of run time sequence.
          First, attack python wrapper - boto3
          Then, all pulumi infra resource roll outs - pulumi
    """

    print("\n\n\n")
    print("Starting Full Attack & Deployment Cleanup\n")
    print("\n\n\n")


    ###
    ### Need to refractor to make user intake more clean & modular
    ###
    clean_user = Cleanup.CleanUser(user="DevopsUser")
    clean_user.execute_cleanup()
    print("\n\n\n")
    print("Deleted all DevopsUser information")
    print("\n\n\n")

    clean_user = Cleanup.CleanUser(user="run_while_u_can")
    clean_user.execute_cleanup()
    print("\n\n\n")
    print("Deleted all run_while_u_can information")
    print("\n\n\n")

    # Cleanup AWS credentials, profiles, and cache
    AWSProfileCleanup.clear_env_vars()
    AWSProfileCleanup.remove_aws_profiles()
    AWSProfileCleanup.clear_aws_cache()
    print("\n\n\n")
    print("Deleted AWS env_vars, profiles, & cache")
    print("\n\n\n")

    # Delete attack results
    delete_enum_folder()
    delete_s3_exfil_folder()
    delete_dynamo_exfil_folder
    print("\n\n\n")
    print("Deleted Attack Results Folder")
    print("\n\n\n")

    # Verify cleanup
    AWSProfileCleanup.verify_cleanup()
    print("\n\n\n")
    print("Post Deploymenyt Cleanup verified successfully")
    print("\n\n\n")

    # Entering 
    subprocess.call("cd /workspaces/Pulumi/Infra && pulumi refresh -s dev -y", shell=True)
    subprocess.call("cd /workspaces/Pulumi/Infra && pulumi destroy -s dev -y", shell=True)
    print("\n\n\n")
    print("Pulumi Deployment cleaned up successfully")
    print("\n\n\n")

    print("\n\n\n")
    print("And just like that the attack and deployment vanished :)")
    print("\n\n\n")





#full_cleanup()
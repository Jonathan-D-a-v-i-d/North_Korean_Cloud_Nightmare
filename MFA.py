import json
import time
import subprocess




class MFASetup:
    """ Handles MFA Creation, Authentication & Validation"""
    def __init__(self, user, mfa_arn, iam_client, sts_client, pulumi_outputs):
        self.user = user
        self.mfa_arn = mfa_arn
        self.iam_client = iam_client
        self.sts_client = sts_client
        self.pulumi_outputs = pulumi_outputs 
        self.mfa_seed_bin_file_path = "/workspaces/Pulumi/Infra/mfa-seed.bin"
        self.mfa_secret = self.extract_mfa_secret()
        self.session_token = None
        self.accesskey_ID = None
        self.secret_access_key = None


    def check_existing_mfa(self):
        """ Check if MFA is already enabled"""
        print(f"\n Checking if MFA is enabled for `{self.user}`...")
        result = subprocess.run(
            f"aws iam list-mfa-devices --user-name {self.user} --query 'MFADevices[0].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        self.mfa_arn = result.stdout.strip()
        if "arn:aws" in self.mfa_arn:
            print(f"MFA is already enabled: {self.mfa_arn}")
            return True
        print("No MFA device found. Proceeding to create a new MFA device...")
        return False
    


    def cleanup_old_mfa(self):
        """ Delete any stale virtual MFA devices"""
        existing_mfa_check = subprocess.run(
            "aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        existing_mfa = existing_mfa_check.stdout.strip()
        if "arn:aws" in existing_mfa:
            print(f"Deleting old MFA device: {existing_mfa}")
            subprocess.run(f"aws iam delete-virtual-mfa-device --serial-number {existing_mfa}", shell=True)
        else:
            print("No stale MFA devices found.")



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
        """Extract MFA Secret from `mfa-seed.bin` (AWS Stores in Base32)"""
        time.sleep(2)  # Give AWS time to sync
        print("\n\n\n") 
        print("Fetching MFA Secret...")
        print("\n\n\n")
        #
        # Thinking of putting potential if statement to create message only on new
        # rollouts by searching the timestamp of the file and time checking it
        # to be less than 1 minute old
        try:
            with open(self.mfa_seed_bin_file_path, "r") as seed_file:
                self.mfa_secret = seed_file.read().strip()  # Read directly, no decoding
            print(f"MFA Secret Retrieved: {self.mfa_secret}")
            return self.mfa_secret
        except Exception as e:
            print(f"ERROR: Could not read MFA seed file: {e}")
            exit(1)


    
    def generate_mfa_codes(self):
        """Generate MFA TOTP codes"""
        print("Ensuring system clock is synchronized...")
        subprocess.run("sudo ntpdate -q time.google.com", shell=True)
        code1 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        time.sleep(30)  # Wait for new OTP
        code2 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        print(f"Auto-Generated MFA Codes: {code1}, {code2}")
        return code1, code2
    
    def enable_mfa(self, code1, code2):
        """ Enable MFA for DevopsUser"""
        print("\n Enabling MFA for DevopsUser...")
        enable_mfa_command = f"""
        aws iam enable-mfa-device --user-name {self.user} \
            --serial-number {self.mfa_arn} \
            --authentication-code1 {code1} --authentication-code2 {code2}
        """
        print(f"Running: {enable_mfa_command}")
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
    def get_pulumi_secret(self,secret_name):
        """Fetch Pulumi secret with --show-secrets"""
        try:
            result = subprocess.run(
                f"pulumi stack output {secret_name} --show-secrets",
                shell=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"ERROR: Failed to retrieve Pulumi secret {secret_name}: {e}")
            exit(1)
    
    def login_as_devops(self):
        """ Log in as DevOpsUser using Access Key + MFA"""
    
        print("\nWaiting for AWS to fully associate MFA device...")
        time.sleep(10)
    
        # Step 1: Verify MFA is linked before attempting login
        validation = subprocess.run([
            "aws", "iam", "list-mfa-devices",
            "--user-name", self.user,
            "--query", "MFADevices[*].SerialNumber",
            "--output", "text"
        ], capture_output=True, text=True)
    
        if "arn:aws" not in validation.stdout:
            print("ERROR: MFA device is NOT linked to DevOpsUser. Exiting...")
            exit(1)
    
        print("MFA device is successfully linked. Proceeding with login.")
    
        #  Step 2: Load DevOpsUser's Access Key & Secret Key **Directly from Pulumi Secrets**
        devops_access_key = self.get_pulumi_secret("devops_access_key_id")
        devops_secret_key = self.get_pulumi_secret("devops_secret_access_key")
    
        print(f"\nDevOps Access Key: {devops_access_key}")
        print(f" DevOps Secret Key: {'*' * len(devops_secret_key)} (Hidden for security)")
    
        if not devops_access_key or not devops_secret_key:
            print(" ERROR: DevOpsUser access key/secret key not found in Pulumi outputs.")
            exit(1)
    
        #  Step 3: Configure AWS CLI Profile for DevOpsUser
        print("\n🔧 Configuring AWS CLI profile for DevOpsUser...")
        subprocess.run(f"aws configure set aws_access_key_id \"{devops_access_key}\" --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set aws_secret_access_key \"{devops_secret_key}\" --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set region us-east-1 --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set output json --profile devopsuser", shell=True)
    
        #  Step 4: Generate MFA Code
        print("\n Requesting session token for DevOpsUser...")
        mfa_code = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
    
        #  Step 5: Call `get_session_token` with MFA
        try:
            session_response = subprocess.run(
                f"aws sts get-session-token --serial-number {self.mfa_arn} --token-code {mfa_code} --profile devopsuser",
                shell=True, capture_output=True, text=True
            )
    
            #  Ensure response is not empty
            if not session_response.stdout.strip():
                print(f"ERROR: Empty response received from AWS STS. Possible MFA setup issue.")
                exit(1)
    
            session_data = json.loads(session_response.stdout)
            creds = session_data.get("Credentials")
    
            if not creds:
                print(f"ERROR: AWS did not return credentials! Response: {session_data}")
                exit(1)

            self.session_token = creds['SessionToken']
            self.accesskey_ID = creds['AccessKeyId']
            self.secret_access_key = creds['SecretAccessKey']

            print("\n\n\n") 
            print(f"{self.user} token retrieved!")
            print(f"Token: {creds['SessionToken']}")
            print("\n\n\n")
            #  Step 6: Export Temporary Session Credentials to AWS CLI Profile
            print("\n Storing temporary MFA session in AWS CLI profile...")
            subprocess.run(f"aws configure set aws_access_key_id \"{creds['AccessKeyId']}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key \"{creds['SecretAccessKey']}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set aws_session_token \"{creds['SessionToken']}\" --profile devopsuser", shell=True)
    
            #  Step 7: Verify the AWS profile with MFA session
            print("\n Verifying AWS profile with MFA session...")
            verify_output = subprocess.run("aws sts get-caller-identity --profile devopsuser", shell=True, capture_output=True, text=True)
    
            if "arn:aws" not in verify_output.stdout:
                print(f"ERROR: Profile verification failed! Response: {verify_output.stderr}")
                exit(1)
    
            print(f"{self.user}'s AWS profile successfully authenticated with MFA!")
    
        except Exception as e:
            print(f"ERROR: MFA authentication failed: {e}")
            exit(1)

            
    def setup_mfa_and_login(self):
        """Full MFA Setup + Login"""
        self.check_existing_mfa()
        self.cleanup_old_mfa()
        self.create_mfa_device()
        self.extract_mfa_secret()
        code1, code2 = self.generate_mfa_codes()
        self.enable_mfa(code1, code2)
        self.login_as_devops()  # Automatically log in after enabling MFA
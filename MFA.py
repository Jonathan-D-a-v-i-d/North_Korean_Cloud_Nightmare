import json
import time
import subprocess
from termcolor import colored




class MFASetup:
    """ Handles MFA Creation, Authentication & Validation"""
    def __init__(self, user, mfa_arn, iam_client, sts_client, infrastructure_outputs):
        self.user = user
        self.mfa_arn = mfa_arn
        self.iam_client = iam_client
        self.sts_client = sts_client
        self.infrastructure_outputs = infrastructure_outputs 
        self.mfa_seed_bin_file_path = "/workspaces/North_Korean_Cloud_Nightmare/Infra/mfa-seed.bin"
        self.mfa_secret = self.extract_mfa_secret()
        self.session_token = None
        self.accesskey_ID = None
        self.secret_access_key = None


    def check_existing_mfa(self):
        """ Check if MFA is already enabled"""
        print(colored(f"[INFO] Checking if MFA is enabled for {self.user}...", "cyan"))
        result = subprocess.run(
            f"aws iam list-mfa-devices --user-name {self.user} --query 'MFADevices[0].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        self.mfa_arn = result.stdout.strip()
        if "arn:aws" in self.mfa_arn:
            print(colored(f"[SUCCESS] MFA is already enabled: {self.mfa_arn}", "green"))
            return True
        print(colored("[INFO] No MFA device found. Proceeding to create a new MFA device...", "yellow"))
        return False
    
    # def cleanup_old_mfa(self):
    #       """ Delete any stale virtual MFA devices **one-by-one** to avoid AWS CLI errors """
    #       existing_mfa_check = subprocess.run(
    #           "aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
    #           shell=True, capture_output=True, text=True
    #       )
    #       existing_mfa_arns = existing_mfa_check.stdout.strip().split()

    #       if not existing_mfa_arns:
    #           print("No stale MFA devices found.")
    #           return  # Exit if no devices found

    #       for mfa_arn in existing_mfa_arns:
    #           print(f"Deleting old MFA device: {mfa_arn}")
    #           delete_result = subprocess.run(
    #               f"aws iam delete-virtual-mfa-device --serial-number {mfa_arn}",
    #               shell=True, capture_output=True, text=True
    #           )
    #           if delete_result.returncode == 0:
    #               print(f"Successfully deleted MFA Device: {mfa_arn}")
    #           else:
    #               print(f"ERROR: Failed to delete MFA Device {mfa_arn} - {delete_result.stderr}")

    # def cleanup_devopsuser_mfa(self):
    #     """ Delete any stale virtual MFA devices associated with 'DevopsUser' """
    #     devops_user_mfa_check = subprocess.run(
    #         "aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
    #         shell=True, capture_output=True, text=True
    #     )
    #     existing_mfa_arns = devops_user_mfa_check.stdout.strip().split()

    #     if not existing_mfa_arns:
    #         print("No stale MFA devices found for DevopsUser.")
    #         return  # Exit if no devices found

    #     for mfa_arn in existing_mfa_arns:
    #         if "DevopsUser" in mfa_arn:  # Ensure only DevopsUser MFA is deleted
    #             print(f"Deleting old MFA device: {mfa_arn}")
    #             delete_result = subprocess.run(
    #                 f"aws iam delete-virtual-mfa-device --serial-number {mfa_arn}",
    #                 shell=True, capture_output=True, text=True
    #             )
    #             if delete_result.returncode == 0:
    #                 print(f"Successfully deleted MFA Device: {mfa_arn}")
    #             else:
    #                 print(f"ERROR: Failed to delete MFA Device {mfa_arn} - {delete_result.stderr}")
    #         else:
    #             print(f"Skipping MFA device {mfa_arn}, not associated with DevopsUser.")


    # def cleanup_devopsuser_mfa(self):
    #     """ Deactivates and deletes any MFA devices associated with 'DevopsUser' """

    #     # Step 1: List MFA devices for DevopsUser
    #     list_mfa_result = subprocess.run(
    #         "aws iam list-mfa-devices --user-name DevopsUser --query 'MFADevices[*].SerialNumber' --output text",
    #         shell=True, capture_output=True, text=True
    #     )

    #     devops_user_mfa_arns = list_mfa_result.stdout.strip().split()

    #     if not devops_user_mfa_arns:
    #         print("No active MFA device found for DevopsUser.")
    #     else:
    #         for mfa_arn in devops_user_mfa_arns:
    #             print(f"Deactivating MFA device: {mfa_arn}")

    #             deactivate_result = subprocess.run(
    #                 f"aws iam deactivate-mfa-device --user-name DevopsUser --serial-number {mfa_arn}",
    #                 shell=True, capture_output=True, text=True
    #             )

    #             if deactivate_result.returncode == 0:
    #                 print(f"Successfully deactivated MFA Device: {mfa_arn}")
    #             else:
    #                 print(f"ERROR: Failed to deactivate MFA Device {mfa_arn} - {deactivate_result.stderr}")
    #                 return  # Exit early if deactivation fails

    #     # Step 2: List all MFA devices in the account (to delete stale devices)
    #     list_all_mfa_result = subprocess.run(
    #         "aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
    #         shell=True, capture_output=True, text=True
    #     )

    #     all_mfa_arns = list_all_mfa_result.stdout.strip().split()

    #     if not all_mfa_arns:
    #         print("No stale MFA devices found.")
    #         return

    #     # Step 3: Delete only unassigned MFA devices related to DevopsUser
    #     for mfa_arn in all_mfa_arns:
    #         if "DevopsUser" in mfa_arn:
    #             print(f"Deleting unassigned MFA device: {mfa_arn}")
    #             delete_result = subprocess.run(
    #                 f"aws iam delete-virtual-mfa-device --serial-number {mfa_arn}",
    #                 shell=True, capture_output=True, text=True
    #             )

    #             if delete_result.returncode == 0:
    #                 print(f"Successfully deleted MFA Device: {mfa_arn}")
    #             else:
    #                 print(f"ERROR: Failed to delete MFA Device {mfa_arn} - {delete_result.stderr}")




    def create_mfa_device(self):
        """Create a Virtual MFA Device"""
        print(colored("[INFO] Creating new Virtual MFA device...", "cyan"))
        create_mfa_command = f"""
        aws iam create-virtual-mfa-device \
            --virtual-mfa-device-name {self.user}-MFA \
            --outfile {self.mfa_seed_bin_file_path} \
            --bootstrap-method Base32StringSeed \
            --query 'VirtualMFADevice.SerialNumber' \
            --output text
        """
        new_mfa_arn = subprocess.run(create_mfa_command, shell=True, capture_output=True, text=True).stdout.strip()
        if not new_mfa_arn:
            print(colored("[ERROR] Failed to create MFA device!", "red"))
            exit(1)
        self.mfa_arn = new_mfa_arn  # Ensure we store the correct ARN
        print(colored(f"[SUCCESS] New MFA device created: {self.mfa_arn}", "green"))
        # Extract MFA Secret **after** MFA creation
        self.mfa_secret = self.extract_mfa_secret()
        # Wait for AWS to fully register the MFA device
        print(colored("[INFO] Waiting for AWS to register the new MFA device...", "yellow"))
        time.sleep(10)



    def extract_mfa_secret(self):
        """Extract MFA Secret from `mfa-seed.bin` (AWS Stores in Base32)"""
        time.sleep(2)  # Give AWS time to sync
        print(colored("[INFO] Fetching MFA Secret...", "cyan"))
        #
        # Thinking of putting potential if statement to create message only on new
        # rollouts by searching the timestamp of the file and time checking it
        # to be less than 1 minute old
        try:
            with open(self.mfa_seed_bin_file_path, "r") as seed_file:
                self.mfa_secret = seed_file.read().strip()  # Read directly, no decoding
            print(colored(f"[SUCCESS] MFA Secret Retrieved: {self.mfa_secret}", "green"))
            return self.mfa_secret
        except Exception as e:
            print(colored(f"[ERROR] Could not read MFA seed file: {e}", "red"))
            exit(1)


    
    def generate_mfa_codes(self):
        """Generate MFA TOTP codes"""
        print(colored("[INFO] Ensuring system clock is synchronized...", "cyan"))
        subprocess.run("sudo ntpdate -q time.google.com", shell=True, capture_output=True, text=True)
        code1 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        time.sleep(30)  # Wait for new OTP
        code2 = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        print(colored(f"[SUCCESS] Auto-Generated MFA Codes: {code1}, {code2}", "green"))
        return code1, code2
    
    def enable_mfa(self, code1, code2):
        """ Enable MFA for DevopsUser"""
        print(colored(f"[INFO] Enabling MFA for {self.user}...", "cyan"))
        enable_mfa_command = f"""
        aws iam enable-mfa-device --user-name {self.user} \
            --serial-number {self.mfa_arn} \
            --authentication-code1 {code1} --authentication-code2 {code2}
        """
        result = subprocess.run(enable_mfa_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(colored(f"[ERROR] MFA enablement failed!\n{result.stderr}", "red"))
            exit(1)
        print(colored("[SUCCESS] MFA enabled successfully! Verifying association...", "green"))
        # Validate that AWS successfully linked the MFA device
        validation_command = f"aws iam list-mfa-devices --user-name {self.user} --query 'MFADevices[*].SerialNumber' --output text"
        validation_result = subprocess.run(validation_command, shell=True, capture_output=True, text=True)
        linked_mfa = validation_result.stdout.strip()
        if linked_mfa and "arn:aws" in linked_mfa:
            print(colored(f"[SUCCESS] MFA Device successfully linked: {linked_mfa}", "green"))
        else:
            print(colored("[ERROR] MFA device was NOT linked. Possible AWS delay or misconfiguration.", "red"))
            exit(1)


    def get_infrastructure_secret(self,secret_name):
        """Fetch infrastructure secret with --show-secrets"""
        try:
            result = subprocess.run(
                f"pulumi stack output {secret_name} --show-secrets",
                shell=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(colored(f"[ERROR] Failed to retrieve infrastructure secret {secret_name}: {e}", "red"))
            exit(1)
    

    def login_with_MFA_session_token(self):
        """ Log in as DevOpsUser using Access Key + MFA"""

        print(colored("[INFO] Waiting for AWS to fully associate MFA device...", "yellow"))
        time.sleep(10)

        # Step 1: Verify MFA is linked before attempting login
        validation = subprocess.run([
            "aws", "iam", "list-mfa-devices",
            "--user-name", self.user,
            "--query", "MFADevices[*].SerialNumber",
            "--output", "text"
        ], capture_output=True, text=True)

        if "arn:aws" not in validation.stdout:
            print(colored(f"[ERROR] MFA device is NOT linked to {self.user}. Exiting...", "red"))
            exit(1)

        print(colored("[SUCCESS] MFA device is successfully linked. Proceeding with login.", "green"))

        #  Step 2: Load DevOpsUser's Access Key & Secret Key **Directly from Infrastructure Secrets**
        print(colored("[INFO] Retrieving DevOps user credentials from infrastructure...", "cyan"))
        devops_access_key = self.get_infrastructure_secret("devops_access_key_id")
        devops_secret_key = self.get_infrastructure_secret("devops_secret_access_key")

        print(colored(f"[SUCCESS] DevOps Access Key: {devops_access_key}", "green"))
        print(colored(f"[SUCCESS] DevOps Secret Key: {'*' * len(devops_secret_key)} (Hidden for security)", "green"))

        if not devops_access_key or not devops_secret_key:
            print(colored("[ERROR] DevOpsUser access key/secret key not found in infrastructure outputs.", "red"))
            exit(1)
    
        #  Step 3: Configure AWS CLI Profile for DevOpsUser
        print(colored("[INFO] Configuring AWS CLI profile for DevOpsUser...", "cyan"))
        subprocess.run(f"aws configure set aws_access_key_id \"{devops_access_key}\" --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set aws_secret_access_key \"{devops_secret_key}\" --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set region us-east-1 --profile devopsuser", shell=True)
        subprocess.run(f"aws configure set output json --profile devopsuser", shell=True)

        #  Step 4: Generate MFA Code
        print(colored("[INFO] Requesting session token for DevOpsUser...", "cyan"))
        mfa_code = subprocess.run(f"oathtool --totp --base32 {self.mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
    
        #  Step 5: Call `get_session_token` with MFA
        try:
            session_response = subprocess.run(
                f"aws sts get-session-token --serial-number {self.mfa_arn} --token-code {mfa_code} --profile devopsuser",
                shell=True, capture_output=True, text=True
            )
    
            #  Ensure response is not empty
            if not session_response.stdout.strip():
                print(colored("[ERROR] Empty response received from AWS STS. Possible MFA setup issue.", "red"))
                exit(1)

            session_data = json.loads(session_response.stdout)
            creds = session_data.get("Credentials")

            if not creds:
                print(colored(f"[ERROR] AWS did not return credentials! Response: {session_data}", "red"))
                exit(1)

            self.session_token = creds['SessionToken']
            self.accesskey_ID = creds['AccessKeyId']
            self.secret_access_key = creds['SecretAccessKey']

            print(colored(f"[SUCCESS] {self.user} session token retrieved!", "green"))
            print(colored(f"[INFO] Token: {creds['SessionToken'][:50]}...", "cyan"))
            #  Step 6: Export Temporary Session Credentials to AWS CLI Profile
            print(colored("[INFO] Storing temporary MFA session in AWS CLI profile...", "cyan"))
            subprocess.run(f"aws configure set aws_access_key_id \"{creds['AccessKeyId']}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set aws_secret_access_key \"{creds['SecretAccessKey']}\" --profile devopsuser", shell=True)
            subprocess.run(f"aws configure set aws_session_token \"{creds['SessionToken']}\" --profile devopsuser", shell=True)
    
            #  Step 7: Verify the AWS profile with MFA session
            print(colored("[INFO] Verifying AWS profile with MFA session...", "cyan"))
            verify_output = subprocess.run("aws sts get-caller-identity --profile devopsuser", shell=True, capture_output=True, text=True)

            if "arn:aws" not in verify_output.stdout:
                print(colored(f"[ERROR] Profile verification failed! Response: {verify_output.stderr}", "red"))
                exit(1)

            print(colored(f"[SUCCESS] {self.user}'s AWS profile successfully authenticated with MFA!", "green", attrs=["bold"]))

        except Exception as e:
            print(colored(f"[ERROR] MFA authentication failed: {e}", "red"))
            exit(1)

            
    def setup_mfa_and_login(self):
        """Full MFA Setup + Login"""
        self.check_existing_mfa()
        #self.cleanup_devopsuser_mfa
        self.create_mfa_device()
        self.extract_mfa_secret()
        code1, code2 = self.generate_mfa_codes()
        self.enable_mfa(code1, code2)
        self.login_with_MFA_session_token()  # Automatically log in after enabling MFA




def delete_virtualMFA_device(session, mfa_arn):
    """
    Deletes a Virtual MFA Device given its ARN using a provided boto3 session.
    
    Parameters:
        session (boto3.Session): An authenticated boto3 session.
        mfa_arn (str): The ARN of the virtual MFA device to delete.

    Returns:
        None
    """
    try:
        iam_client = session.client('iam')

        print(colored(f"[INFO] Attempting to delete MFA Device: {mfa_arn}...", "cyan"))
        iam_client.delete_virtual_mfa_device(SerialNumber=mfa_arn)
        print(colored(f"[SUCCESS] Successfully deleted MFA Device: {mfa_arn}", "green"))

    except iam_client.exceptions.NoSuchEntityException:
        print(colored(f"[ERROR] MFA Device {mfa_arn} does not exist or was already deleted.", "red"))
    except Exception as e:
        print(colored(f"[ERROR] Failed to delete MFA Device {mfa_arn}: {e}", "red"))

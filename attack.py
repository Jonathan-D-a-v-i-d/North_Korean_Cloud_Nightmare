import boto3
import json
import pyqrcode
import time
import subprocess
import base64
import os

class Attack:
    def __init__(self, region="us-east-1"):
        """Initialize AWS Clients and Fetch Pulumi Outputs"""
        self.iam_client = boto3.client("iam", region_name=region)

        # ✅ Load Pulumi Outputs to get AWS Resource Names
        with open("Infra/forrester-2025-output.json", "r") as file:
            self.pulumi_outputs = json.load(file)

        self.devops_user = "DevopsUser"
        self.mfa_arn = self.pulumi_outputs.get("devops_user_mfa_arn")  # Pulumi should export this!


    def MFA_phishing_login(self):
        """🛑 Ensure MFA is Set Up Properly"""
        print("\n🔍 Checking if MFA is already enabled for DevopsUser...")

        # ✅ Check existing MFA devices
        result = subprocess.run(
            f"aws iam list-mfa-devices --user-name {self.devops_user} --query 'MFADevices[0].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        self.mfa_arn = result.stdout.strip()

        if self.mfa_arn and self.mfa_arn != "None":
            print(f"✅ MFA is already enabled for {self.devops_user}: {self.mfa_arn}")
            return

        print("❌ No MFA device found. Creating a new Virtual MFA Device...")

        # ✅ Ensure no stale MFA devices exist
        existing_mfa_check = subprocess.run(
            f"aws iam list-virtual-mfa-devices --query 'VirtualMFADevices[*].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        if "arn:aws" in existing_mfa_check.stdout:
            print(f"🗑️ Deleting old MFA device: {self.mfa_arn}")
            subprocess.run(f"aws iam delete-virtual-mfa-device --serial-number {self.mfa_arn}", shell=True)

        # ✅ Create new MFA device
        create_mfa_command = f"""
        aws iam create-virtual-mfa-device \
            --virtual-mfa-device-name {self.devops_user}MFA \
            --outfile mfa-seed.bin \
            --bootstrap-method Base32StringSeed \
            --query 'VirtualMFADevice.SerialNumber' \
            --output text
        """
        self.mfa_arn = subprocess.run(create_mfa_command, shell=True, capture_output=True, text=True).stdout.strip()

        if not self.mfa_arn:
            print("❌ ERROR: Failed to create MFA device!")
            exit(1)

        print(f"✅ New MFA device created: {self.mfa_arn}")

        # ✅ Extract MFA Secret
        time.sleep(2)  # Give AWS time to sync
        print("\n🔍 Fetching MFA Secret for DevopsUser...")

        try:
            with open("mfa-seed.bin", "rb") as seed_file:
                secret_bytes = seed_file.read()
                mfa_secret = base64.b32encode(secret_bytes).decode().strip()
        except Exception as e:
            print(f"❌ ERROR: Could not read MFA seed file: {e}")
            exit(1)

        print(f"✅ MFA Secret Retrieved: {mfa_secret}")

        # ✅ Generate two valid OTP codes
        print("⏳ Ensuring system clock is synchronized...")
        subprocess.run("sudo ntpdate -q time.google.com", shell=True)

        code1 = subprocess.run(f"oathtool --totp --base32 {mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()
        time.sleep(30)  # Wait for new OTP
        code2 = subprocess.run(f"oathtool --totp --base32 {mfa_secret}", shell=True, capture_output=True, text=True).stdout.strip()

        print(f"🔢 Auto-Generated MFA Codes: {code1}, {code2}")

        # ✅ Enable MFA for DevopsUser
        enable_mfa_command = f"""
        aws iam enable-mfa-device --user-name {self.devops_user} \
            --serial-number {self.mfa_arn} \
            --authentication-code1 {code1} --authentication-code2 {code2}
        """
        subprocess.run(enable_mfa_command, shell=True)

        # ✅ Verify MFA is enabled
        final_check = subprocess.run(
            f"aws iam list-mfa-devices --user-name {self.devops_user} --query 'MFADevices[0].SerialNumber' --output text",
            shell=True, capture_output=True, text=True
        )
        final_mfa_serial = final_check.stdout.strip()

        if final_mfa_serial and final_mfa_serial != "None":
            print(f"\n✅ MFA successfully enabled for {self.devops_user}: {final_mfa_serial}")
        else:
            print("\n❌ ERROR: MFA setup failed! Exiting...")
            exit(1)



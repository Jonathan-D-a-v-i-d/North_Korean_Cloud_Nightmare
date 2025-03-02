import json
import sys
import os
import tqdm
from time import sleep
import time
import subprocess


def validate_pulumi_outputs_after_rollout(pulumi_stack_output_file):
    # ✅ Required Pulumi Outputs
    REQUIRED_KEYS = [
        "CustomerOrdersTable",
        "CustomerSSNTable",
        "admin_user_arn",
        "config_files_bucket",
        "customer_data_bucket",
        "devops_user_arn",
        "gd_detector_id",
        "payment_data_bucket",
        "regular_buckets"
    ]

    try:
        with open(pulumi_stack_output_file, "r") as file:
            outputs = json.load(file)

        # 🔹 Check for missing keys
        missing_keys = [key for key in REQUIRED_KEYS if key not in outputs]
        if missing_keys:
            print(f"❌ ERROR: Missing Pulumi outputs: {missing_keys}")
            sys.exit(1)

        print("✅ Pulumi deployment validated successfully. Proceeding to data population...")
        return True

    except FileNotFoundError:
        print(f"❌ ERROR: {pulumi_stack_output_file} not found. Did Pulumi fail?")
        sys.exit(1)



# if __name__ == "__main__":
#     if validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="forrester-2025-output.json"):
#         print("✅ Validation passed! Moving to the next stage...")








def wait_for_output_file():
    sleep_duration = 5
    output_file = "/workspaces/Pulumi/Infra/forrester-2025-output.json"  # FIXED PATH

    with tqdm.tqdm(total=sleep_duration, desc="Validating Deployment") as pbar:
        while sleep_duration > 0:
            if os.path.exists(output_file):
                print(f"✅ File '{output_file}' found!")
                return  # Stop waiting if file exists
            
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval

    print(f"❌ ERROR: {output_file} not found after waiting.")
    sys.exit(1)  # Exit if file was never found







import time
import tqdm

def attack_execution_duration(minutes: float = 0, seconds: float = 0, description: str = None):
    """
    ⏳ Displays a tqdm progress bar to simulate attack execution time.

    Parameters:
        - minutes (float, optional): The duration in minutes for the attack execution. Default is 0.
        - seconds (float, optional): The duration in seconds for the attack execution. Default is 0.
        - description (str, optional): Custom description for the attack progress.
    """
    total_seconds = (minutes * 60) + seconds  # Convert minutes to seconds and sum

    if total_seconds <= 0:
        print("⚠️ Duration must be greater than 0 seconds.")
        return

    # ✅ Automatically format description if not provided
    if description is None:
        description = f"Executing attack for {minutes}m {seconds}s..."

    print(f"\n🔥 {description} (Estimated time: {minutes}m {seconds}s)")

    with tqdm.tqdm(total=total_seconds, desc="⏳ Attack Execution Progress", 
                   bar_format="{l_bar}{bar} [ {elapsed}/{remaining} ]") as pbar:
        for _ in range(int(total_seconds)):
            time.sleep(1)  # Sleep for 1 second
            pbar.update(1)  # Update progress bar

    print("\n✅ Attack execution time elapsed. Proceeding with cleanup...")

# Example usages:
# attack_execution_duration(minutes=1)      # Executes for 1 minute
# attack_execution_duration(seconds=30)     # Executes for 30 seconds
# attack_execution_duration(minutes=1, seconds=30)  # Executes for 1 minute 30 seconds




def progress_bar(seconds):
    """⏳ Display a progress bar while waiting for AWS to propagate MFA registration"""
    print("\n⏳ Waiting for AWS to propagate MFA registration...")
    for _ in tqdm.tqdm(range(seconds), desc="MFA Propagation", unit="s", ncols=80):
        time.sleep(1)






def validate_aws_keys(access_key, secret_key):
    """Validates AWS keys using AWS CLI."""
    print("\n🔍 Validating new AWS credentials...")

    env_vars = {
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key
    }

    try:
        result = subprocess.run(
            f'aws sts get-caller-identity',
            shell=True,  # Enables execution as a full shell command
            env=env_vars,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ AWS keys are valid:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Could not validate AWS credentials: {e.stderr}")
        return False



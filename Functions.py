import json
import sys
import os
import tqdm
from time import sleep
import time


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



if __name__ == "__main__":
    if validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="forrester-2025-output.json"):
        print("✅ Validation passed! Moving to the next stage...")








def wait_for_output_file():
    sleep_duration = 5
    output_file = "Infra/forrester-2025-output.json"  # FIXED PATH

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







def attack_execution_duration(minutes: int, description: str = None):
    """
    ⏳ Displays a tqdm progress bar to simulate attack execution time.

    Parameters:
        - minutes (int): The duration in minutes for the attack execution.
        - description (str, optional): Custom description for the attack progress.
    """
    seconds = minutes * 60  # Convert minutes to seconds

    # ✅ Automatically format description if not provided
    if description is None:
        description = f"Executing attack for {minutes} minutes..."

    print(f"\n🔥 {description} (Estimated time: {minutes} minutes)")

    with tqdm.tqdm(total=seconds, desc="⏳ Attack Execution Progress", bar_format="{l_bar}{bar} [ {elapsed}/{remaining} ]") as pbar:
        for _ in range(seconds):
            time.sleep(1)  # Sleep for 1 second
            pbar.update(1)  # Update progress bar
            
    print("\n✅ Attack execution time elapsed. Proceeding with cleanup...")


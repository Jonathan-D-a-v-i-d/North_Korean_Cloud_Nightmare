import os
import json




PULUMI_OUTPUT_PATH = "/workspaces/Pulumi/Infra/forrester-2025-output.json"

def load_pulumi_outputs():
    """🔍 Load Pulumi outputs and return as a dictionary"""
    if not os.path.exists(PULUMI_OUTPUT_PATH):
        raise RuntimeError(f"ERROR: Pulumi output file '{PULUMI_OUTPUT_PATH}' not found. Did you run 'pulumi up'?")

    try:
        with open(PULUMI_OUTPUT_PATH, "r") as file:
            pulumi_outputs = json.load(file)

        if not isinstance(pulumi_outputs, dict):
            raise RuntimeError("ERROR: Pulumi output file is corrupted or not in JSON format.")

        return pulumi_outputs  # Return dictionary of outputs

    except json.JSONDecodeError:
        raise RuntimeError(f"ERROR: Pulumi output file '{PULUMI_OUTPUT_PATH}' contains invalid JSON. Check Pulumi execution.")
    except Exception as e:
        raise RuntimeError(f"ERROR: Failed to load Pulumi outputs: {str(e)}")


def get_pulumi_output(key):
    """🔍 Retrieve a specific value from Pulumi outputs"""
    pulumi_outputs = load_pulumi_outputs()  # Ensure outputs are loaded
    return pulumi_outputs.get(key, f"ERROR: {key} not found in Pulumi outputs.")






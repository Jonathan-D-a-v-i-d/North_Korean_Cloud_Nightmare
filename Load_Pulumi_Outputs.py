import os
import json




OUTPUT_PATH = "/workspaces/North_Korean_Cloud_Nightmare/Infra/forrester-2025-output.json"

def load_infrastructure_outputs():
    """🔍 Load infrastructure outputs and return as a dictionary"""
    if not os.path.exists(OUTPUT_PATH):
        raise RuntimeError(f"ERROR: Output file '{OUTPUT_PATH}' not found. Did you run infrastructure deployment?")

    try:
        with open(OUTPUT_PATH, "r") as file:
            infrastructure_outputs = json.load(file)

        if not isinstance(infrastructure_outputs, dict):
            raise RuntimeError("ERROR: Output file is corrupted or not in JSON format.")

        return infrastructure_outputs  # Return dictionary of outputs

    except json.JSONDecodeError:
        raise RuntimeError(f"ERROR: Output file '{OUTPUT_PATH}' contains invalid JSON. Check infrastructure execution.")
    except Exception as e:
        raise RuntimeError(f"ERROR: Failed to load infrastructure outputs: {str(e)}")


def get_infrastructure_output(key):
    """🔍 Retrieve a specific value from infrastructure outputs"""
    infrastructure_outputs = load_infrastructure_outputs()  # Ensure outputs are loaded
    return infrastructure_outputs.get(key, f"ERROR: {key} not found in infrastructure outputs.")






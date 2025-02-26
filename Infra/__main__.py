"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import json
import random
from faker import Faker

config = pulumi.Config()
region = config.get("aws:region") or "us-east-1"

# ✅ Initialize Faker
fake = Faker()


#               _           _         _    _               
#      /\      | |         (_)       | |  | |              
#     /  \   __| |_ __ ___  _ _ __   | |  | |___  ___ _ __ 
#    / /\ \ / _` | '_ ` _ \| | '_ \  | |  | / __|/ _ \ '__|
#   / ____ \ (_| | | | | | | | | | | | |__| \__ \  __/ |   
#  /_/    \_\__,_|_| |_| |_|_|_| |_|  \____/|___/\___|_|   

# ---------------------- #                                                                                        
# Creates Admin IAM User #
# ---------------------- #
admin_user = aws.iam.User("AdminUser", name="AdminUser")
# ------------------------------------------------- #
# Attaches AdministratorAccess policy to Admin user #
# ------------------------------------------------- #
admin_user_admin_access = aws.iam.UserPolicyAttachment("AdminUserAdminAccess",
    user=admin_user.name,
    policy_arn="arn:aws:iam::aws:policy/AdministratorAccess"
)



#   _____              ____              _    _               
#  |  __ \            / __ \            | |  | |              
#  | |  | | _____   _| |  | |_ __  ___  | |  | |___  ___ _ __ 
#  | |  | |/ _ \ \ / / |  | | '_ \/ __| | |  | / __|/ _ \ '__|
#  | |__| |  __/\ V /| |__| | |_) \__ \ | |__| \__ \  __/ |   
#  |_____/ \___| \_/  \____/| .__/|___/  \____/|___/\___|_|   
#                           | |                               
#                           |_|               

# ------------------- #                                                                                        
# Creates DevOps User #
# ------------------- #   
devops_user = aws.iam.User("DevopsUser", name="DevopsUser")

# --------------------------------- #                                                                                        
# Creates Access Key for DevopsUser #
# --------------------------------- #  
devops_access_key = aws.iam.AccessKey("DevopsUserAccessKey", user=devops_user.name)

# ------------------------------------------ #                                                                                        
# Creates DevOps Like Policy for DevOps User #
# ------------------------------------------ #
"""
Note: This attack vector leverages admin policy for unrestricted
        - s3
        - DynamoDB 
      access, so these must not be part of Devops User's policy
""" 
devops_policy = aws.iam.Policy("DevopsPolicy",
    name="DevopsPolicy",
    description="Access policy for devops-related AWS services",
    policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "elasticbeanstalk:*",
                "cloudwatch:*",
                "autoscaling:*"
            ],
            "Resource": "*"
        }]
    }"""
)
# --------------------------------------- #
# Attaches the DevopsPolicy to DevopsUser #
# --------------------------------------- #
devops_user_policy_attachment = aws.iam.UserPolicyAttachment("DevopsUserPolicyAttachment",
    user=devops_user.name,
    policy_arn=devops_policy.arn
)

# ✅ Define MFA & Session Token Management Policy for DevOps User
devops_mfa_policy = aws.iam.Policy("DevopsMFASetupPolicy",
    name="DevopsMFASetupPolicy",
    description="Allows DevopsUser to manage their own MFA and obtain session tokens",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:CreateVirtualMFADevice",
                    "iam:EnableMFADevice",
                    "iam:ResyncMFADevice",
                    "iam:ListMFADevices",
                    "iam:DeactivateMFADevice",
                    "iam:DeleteVirtualMFADevice",
                    "sts:GetSessionToken"  
                ],
                "Resource": "*"
            }
        ]
    })
)


# ✅ Attach the MFA Management Policy to DevOps User
devops_user_mfa_attachment = aws.iam.UserPolicyAttachment("DevopsUserMFAAttachment",
    user=devops_user.name,
    policy_arn=devops_mfa_policy.arn
)


# ✅ Define a new policy to allow session authentication with MFA
devops_mfa_session_policy = aws.iam.Policy("DevopsMFASessionPolicy",
    name="DevopsMFASessionPolicy",
    description="Allows DevOpsUser to assume session token with MFA",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sts:GetSessionToken"
                ],
                "Resource": "*",
                "Condition": {
                    "Bool": {"aws:MultiFactorAuthPresent": "true"}
                }
            }
        ]
    })
)

# ✅ Attach the policy to DevOpsUser
devops_user_mfa_session_attachment = aws.iam.UserPolicyAttachment("DevopsUserMFASessionAttachment",
    user=devops_user.name,
    policy_arn=devops_mfa_session_policy.arn
)




# ✅ Create Virtual MFA Device for DevopsUser
devops_user_mfa = aws.iam.VirtualMfaDevice("DevopsUserMFA",
    virtual_mfa_device_name="DevopsUserMFA",
    tags={"Name": "DevopsUserMFA"}
)





#       ____    ____             _        _       
#      |___ \  |  _ \           | |      | |      
#   ___  __) | | |_) |_   _  ___| | _____| |_ ___ 
#  / __||__ <  |  _ <| | | |/ __| |/ / _ \ __/ __|
#  \__ \___) | | |_) | |_| | (__|   <  __/ |_\__ \
#  |___/____/  |____/ \__,_|\___|_|\_\___|\__|___/

#######################################################                                                
############## NON-SENSITIVE COMPANY DATA #############
#######################################################
"""
Note: Made after Q1-4 naming convention of company quarterly information
      EX: Bucket 1 - company-data-Q1-2024
      EX: Bucket 2 - company-data-Q2-2024
      EX: Bucket 3 - company-data-Q3-2024
      EX: Bucket 4 - company-data-Q4-2024
"""                                           
# --------------------------------------------------- #
# Creates 4 S3 buckets for non-sensitive company data #
# --------------------------------------------------- #
regular_buckets = [aws.s3.Bucket(f"company-data-Q{i}-2024", force_destroy=True) for i in range(1, 5)]
###################################################                                                
############## SENSITIVE COMPANY DATA #############
###################################################
"""
Note: Creating:
        Bucket - Configeration_Files
        Bucket - Customer_Data
        Bucket - Payment_Data
      to be populated afterwards by larger python wrapper
"""
# ---------------------------------------- #
# Create S3 bucket for Configuration Files #
# ---------------------------------------- #
config_files_bucket = aws.s3.Bucket("configuration-files", force_destroy=True)
# ---------------------------------- #
# Create S3 bucket for Customer Data #
# ---------------------------------- #
customer_data_bucket = aws.s3.Bucket("customer-data", force_destroy=True)
# --------------------------------- #
# Create S3 bucket for Payment Data #
# --------------------------------- #
payment_data_bucket = aws.s3.Bucket("payment-data", force_destroy=True)







#   _____                                    _____  ____  
#  |  __ \                                  |  __ \|  _ \ 
#  | |  | |_   _ _ __   __ _ _ __ ___   ___ | |  | | |_) |
#  | |  | | | | | '_ \ / _` | '_ ` _ \ / _ \| |  | |  _ < 
#  | |__| | |_| | | | | (_| | | | | | | (_) | |__| | |_) |
#  |_____/ \__, |_| |_|\__,_|_| |_| |_|\___/|_____/|____/ 
#           __/ |                                         
#          |___/                                          

# Regular Orders Table (Non-Sensitive Information)
orders_table = aws.dynamodb.Table("CustomerOrdersTable",
    attributes=[aws.dynamodb.TableAttributeArgs(name="ID", type="S")],
    hash_key="ID",
    billing_mode="PAY_PER_REQUEST"
)

# Sensitive Data Table (High-Value Target)
ssn_table = aws.dynamodb.Table("CustomerSSNTable",
    attributes=[aws.dynamodb.TableAttributeArgs(name="ID", type="S")],
    hash_key="ID",
    billing_mode="PAY_PER_REQUEST"
)








# ✅ Generate Fake Data
fake_config_data = {
    "system": "Enterprise App",
    "config_version": "1.2.3",
    "allowed_ips": [f"192.168.1.{i}" for i in range(1, 101)]
}

fake_customer_data = [
    {
        "id": i,
        "name": fake.name(),
        "email": f"{fake.first_name().lower()}{random.randint(1,99)}@{random.choice(['gmail.com', 'yahoo.com'])}"
    }
    for i in range(1, 101)
]

fake_payment_data = [
    {
        "id": i,
        "card": f"{random.choice(['4111', '5500'])}-XXXX-XXXX-{random.randint(1000,9999)}",
        "cvv": f"{random.randint(100,999)}"
    }
    for i in range(1, 101)
]

# ✅ Upload Data to S3 Using Pulumi
aws.s3.BucketObject("config-file",
    bucket=config_files_bucket.id,
    key="config.json",
    content=json.dumps(fake_config_data, indent=4)
)

aws.s3.BucketObject("customer-file",
    bucket=customer_data_bucket.id,
    key="customers.json",
    content=json.dumps(fake_customer_data, indent=4)
)

aws.s3.BucketObject("payment-file",
    bucket=payment_data_bucket.id,
    key="payments.json",
    content=json.dumps(fake_payment_data, indent=4)
)

# ✅ Populate DynamoDB Tables Using Pulumi
for i in range(1, 11):
    aws.dynamodb.TableItem(f"order-{i}",
        table_name=orders_table.name,
        hash_key="ID",
        item=json.dumps({
            "ID": {"S": str(1000 + i)},
            "OrderDate": {"S": fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d")},
            "CustomerName": {"S": fake.name()},
            "ItemPurchased": {"S": random.choice(["Laptop", "Keyboard", "Monitor", "Mouse", "Tablet", "Phone", "Headphones", "Charger"])}
        })
    )

    aws.dynamodb.TableItem(f"ssn-{i}",
        table_name=ssn_table.name,
        hash_key="ID",
        item=json.dumps({
            "ID": {"S": str(2000 + i)},
            "CustomerName": {"S": fake.name()},
            "SSN": {"S": f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"},
            "CreditCard": {"S": f"{random.choice(['4111', '5500'])}-XXXX-XXXX-{random.randint(1000,9999)}"}
        })
    )




















# Enable GuardDuty
gd_detector = aws.guardduty.Detector("gd_detector", enable=True)



"""
#    _____ _                 _ _______        _ _ 
#   / ____| |               | |__   __|      (_) |
#  | |    | | ___  _   _  __| |  | |_ __ __ _ _| |
#  | |    | |/ _ \| | | |/ _` |  | | '__/ _` | | |
#  | |____| | (_) | |_| | (_| |  | | | | (_| | | |
#   \_____|_|\___/ \__,_|\__,_|  |_|_|  \__,_|_|_|
                                                
# ----------------------------------------- #                                                
# Creating s3 Bucket for CloudTrail Logging #
# ----------------------------------------- #  
cloudtrail_log_bucket = aws.s3.Bucket("cloudtrail-log-bucket", force_destroy=True)
# ---------------------------------------------- #                                                
# Enable CloudTrail logging to track IAM changes #
# ---------------------------------------------- # 
cloudtrail = aws.cloudtrail.Trail("cloudtrail",
    name="cloudtrail",
    s3_bucket_name=cloudtrail_log_bucket.bucket,
    include_global_service_events=True,
    is_multi_region_trail=True,
    enable_logging=True
)
"""






# Outputs
pulumi.export("admin_user_arn", admin_user.arn)
pulumi.export("devops_user_arn", devops_user.arn)
pulumi.export("devops_access_key_id", devops_access_key.id)
pulumi.export("devops_secret_access_key", devops_access_key.secret)
pulumi.export("regular_buckets", [bucket.bucket for bucket in regular_buckets])
pulumi.export("config_files_bucket", config_files_bucket.bucket)
pulumi.export("customer_data_bucket", customer_data_bucket.bucket)
pulumi.export("payment_data_bucket", payment_data_bucket.bucket)
pulumi.export("CustomerOrdersTable", orders_table.name)
pulumi.export("CustomerSSNTable", ssn_table.name)
pulumi.export("gd_detector_id", gd_detector.id)
pulumi.export("devops_user_mfa_policy_arn", devops_mfa_policy.arn)
pulumi.export("devops_user_mfa_arn", devops_user_mfa.arn)
# pulumi.export("cloudtrail_id", cloudtrail.id)


"""An AWS Python program for North Korean Cloud Nightmare demo"""

import pulumi
import pulumi_aws as aws
import json
import random
from faker import Faker

config = pulumi.Config()
region = config.get("aws:region") or "us-east-1"

#  Initialize Faker
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









# #   _____                              _______                   
# #  |  __ \                            |__   __|                  
# #  | |  | | _____   _____  _ __  ___     | | ___  __ _ _ __ ___  
# #  | |  | |/ _ \ \ / / _ \| '_ \/ __|    | |/ _ \/ _` | '_ ` _ \ 
# #  | |__| |  __/\ V / (_) | |_) \__ \    | |  __/ (_| | | | | | |
# #  |_____/ \___| \_/ \___/| .__/|___/    |_|\___|\__,_|_| |_| |_|
# #                         | |                                    
# #                         |_|                                    
# # ------------------------------------------- #
# #  Create DevOps Users for Larger Devops Team #
# # ------------------------------------------- #
# """
# These users are the backdrop to the larger vector, in that user: DevopUser
# is compromised via access-key purchase & MFA pfishing, then creates a user
# and attaches an inline policy aloowing it to remove MFA device, and will 
# remove the virtual MFA device of each of his team members to initialize 
# MFA Tampering DDOS as part of the larger vector.
# """

# #devops_users = [aws.iam.User(_) for _ in ["DevopsDeploy", "DevopsAutomation", "DevopsMonitor", "DevopsPipeline"]]
# devops_users = []
# devops_mfa_devices = []

# # 4 Users in addition to user:DevopsUser based on common Devops roles\functionalities
# usernames = ["DevopsDeploy", "DevopsAutomation", "DevopsMonitor", "DevopsPipeline"]

# for username in usernames:
#     # Create user
#     user = aws.iam.User(username)
#     devops_users.append(user)
#     # Create Access Key
#     access_key = aws.iam.AccessKey(f"{username}-access-key", user=user.name)
#     # Create Virtual MFA Device
#     mfa_device = aws.iam.VirtualMfaDevice(f"{username}-mfa", virtual_mfa_device_name=user.name)
#     devops_mfa_devices.append(mfa_device)
#     # Attach MFA Policy (Allow ONLY sts:GetSessionToken with MFA)
#     mfa_enforcement_policy = aws.iam.UserPolicy(
#         f"{username}-mfa-policy",
#         user=user.name,
#         policy=pulumi.Output.all().apply(
#             lambda _: json.dumps({
#                 "Version": "2012-10-17",
#                 "Statement": [
#                     {
#                         "Effect": "Deny",
#                         "NotAction": "sts:GetSessionToken",
#                         "Resource": "*",
#                         "Condition": {
#                             "BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}
#                         }
#                     }
#                 ]
#             })
#         )
#     )


# usernames = ["DevopsDeploy", "DevopsAutomation", "DevopsMonitor", "DevopsPipeline"]

# for username in usernames:
#     # Create IAM User
#     user = aws.iam.User(username)

#     # Export User ARN
#     pulumi.export(f"{username}_arn", user.arn)

#     # Create Access Key
#     access_key = aws.iam.AccessKey(f"{username}-access-key", user=user.name)

#     # Export Access Key ID & Secret
#     pulumi.export(f"{username}_access_key_id", access_key.id)
#     pulumi.export(f"{username}_secret_access_key", access_key.secret)

#     # Create Virtual MFA Device
#     mfa_device = aws.iam.VirtualMfaDevice(f"{username}-mfa", virtual_mfa_device_name=user.name)

#     # Export MFA Device ARN
#     pulumi.export(f"{username}_mfa_arn", mfa_device.arn)

#     # Attach MFA Enforcement Policy (Deny actions if MFA is not used)
#     mfa_enforcement_policy = aws.iam.UserPolicy(
#         f"{username}-mfa-policy",
#         user=user.name,
#         policy=pulumi.Output.all().apply(
#             lambda _: json.dumps({
#                 "Version": "2012-10-17",
#                 "Statement": [
#                     {
#                         "Effect": "Deny",
#                         "NotAction": "sts:GetSessionToken",
#                         "Resource": "*",
#                         "Condition": {
#                             "BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}
#                         }
#                     }
#                 ]
#             })
#         )
#     )





# devops_deploy = aws.iam.User("DevopsDeploy", name="DevopsDeploy")
devops_deploy = aws.iam.User("DevopsDeploy")
devops_deploy_mfa =  aws.iam.VirtualMfaDevice("DevopsDeploy",
    virtual_mfa_device_name="DevopsDeploy",
    tags={"Name": "DevopsDeploy"}    
)
# devops_automation = aws.iam.User("DevopsAutomation", name="DevopsAutomation")
devops_automation = aws.iam.User("DevopsAutomation")
devops_automation_mfa =  aws.iam.VirtualMfaDevice("DevopsAutomation",
    virtual_mfa_device_name="DevopsAutomation",
    tags={"Name": "DevopsAutomation"}    
)
# devops_monitor = aws.iam.User("DevopsMonitor", name="DevopsMonitor")
devops_monitor = aws.iam.User("DevopsMonitor")
devops_monitor_mfa =  aws.iam.VirtualMfaDevice("DevopsMonitor",
    virtual_mfa_device_name="DevopsMonitor",
    tags={"Name": "DevopsMonitor"}    
)
# devops_pipeline = aws.iam.User("DevopsPipeline", name="DevopsPipeline")
devops_pipeline = aws.iam.User("DevopsPipeline")
devops_pipeline_mfa =  aws.iam.VirtualMfaDevice("DevopsPipeline",
    virtual_mfa_device_name="DevopsPipeline",
    tags={"Name": "DevopsPipeline"}    
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
# devops_user = aws.iam.User("DevopsUser", name="DevopsUser")
devops_user = aws.iam.User("DevopsUser")
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
# DevOps Policy - Allows user creation & policy attachment
devops_policy = aws.iam.Policy(
    "DevopsPolicy",
    name="DevopsPolicy",
    description="Extended permissions for DevOpsUser",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                # Allow listing all EC2 instances
                {
                    "Effect": "Allow",
                    "Action": ["ec2:DescribeInstances"],
                    "Resource": "*"
                },
                # Allow listing S3 buckets but no modifications
                {
                    "Effect": "Allow",
                    "Action": ["s3:ListAllMyBuckets"],
                    "Resource": "*"
                },
                # Allow DevOpsUser to enumerate IAM users & policies
                {
                    "Effect": "Allow",
                    "Action": ["iam:ListUsers", "iam:ListPolicies"],
                    "Resource": "*"
                },
                # Allow DevOpsUser to create users, attach policies, and pass roles
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:CreateUser",
                        "iam:AttachUserPolicy",
                        "iam:PutUserPolicy",
                        "iam:PassRole"
                    ],
                    "Resource": "arn:aws:iam::*:user/*"
                },
                # Allow DevOpsUser to create and manage access keys
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:CreateAccessKey",
                        "iam:UpdateAccessKey",
                        "iam:DeleteAccessKey",
                        "iam:ListAccessKeys"
                    ],
                    "Resource": "arn:aws:iam::*:user/*"
                },
                # Allow DevOpsUser to modify and delete created users
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:DeleteUser",
                        "iam:UpdateUser"
                    ],
                    "Resource": "arn:aws:iam::*:user/*"
                },
                # Allow full DynamoDB enumeration (LIST + READ actions)
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:ListTables",
                        "dynamodb:DescribeTable",
                        "dynamodb:Scan",
                        "dynamodb:Query",
                        "dynamodb:GetItem",
                        "dynamodb:BatchGetItem"
                    ],
                    "Resource": "*"
                }
            ]
        },
        indent=4  # Formats JSON output with indentation for better readability
    )
)


# --------------------------------------- #
# Attaches the DevopsPolicy to DevopsUser #
# --------------------------------------- #
devops_user_policy_attachment = aws.iam.UserPolicyAttachment("DevopsUserPolicyAttachment",
    user=devops_user.name,
    policy_arn=devops_policy.arn
)

#  Define MFA & Session Token Management Policy for DevOps User
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


# Attach the MFA Management Policy to DevOps User
devops_user_mfa_attachment = aws.iam.UserPolicyAttachment("DevopsUserMFAAttachment",
    user=devops_user.name,
    policy_arn=devops_mfa_policy.arn
)

# S3/DynamoDB Attack Policies
devops_s3_policy = aws.iam.Policy("DevopsS3Policy",
    name="DevopsS3Policy",
    description="Grants full access to all S3 buckets",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{ "Effect": "Allow", "Action": "s3:*", "Resource": "*" }]
    })
)

devops_dynamodb_policy = aws.iam.Policy("DevopsDynamoDBPolicy",
    name="DevopsDynamoDBPolicy",
    description="Grants full access to DynamoDB",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{ "Effect": "Allow", "Action": "dynamodb:*", "Resource": "*" }]
    })
)



# Define a new policy to allow session authentication with MFA
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

# Attach the policy to DevOpsUser
devops_user_mfa_session_attachment = aws.iam.UserPolicyAttachment("DevopsUserMFASessionAttachment",
    user=devops_user.name,
    policy_arn=devops_mfa_session_policy.arn
)




# Create Virtual MFA Device for DevopsUser
# devops_user_mfa = aws.iam.VirtualMfaDevice("DevopsUserMFA",
#     virtual_mfa_device_name="DevopsUserMFA",
#     tags={"Name": "DevopsUserMFA"}
# )





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








#  Generate Fake Data
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

# Upload Data to S3
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

# Populate DynamoDB Tables
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
# Fetch AWS Account ID dynamically
aws_account_id = aws.get_caller_identity().account_id
# -------------------------------------- #                                                
# Define the CloudTrail S3 bucket policy #
# -------------------------------------- # 
cloudtrail_bucket_policy = aws.s3.BucketPolicy(
    "cloudtrail-bucket-policy",
    bucket=cloudtrail_log_bucket.id,  # Attach policy to this bucket
    policy=pulumi.Output.all(cloudtrail_log_bucket.id, aws_account_id).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck20150319",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:GetBucketAcl",
                    "Resource": f"arn:aws:s3:::{args[0]}"  # ✅ Fix: Dynamically resolve bucket ARN
                },
                {
                    "Sid": "AWSCloudTrailWrite20150319",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": "s3:PutObject",
                    "Resource": f"arn:aws:s3:::{args[0]}/AWSLogs/{args[1]}/*",  # ✅ Fix: Resolve AWS account ID dynamically
                    "Condition": {
                        "StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}
                    }
                }
            ]
        })
    )
)
# ---------------------------------------------- #                                                
# Enable CloudTrail logging to track IAM changes #
# ---------------------------------------------- # 
cloudtrail = aws.cloudtrail.Trail("cloudtrail",
    name="cloudtrail",
    s3_bucket_name=cloudtrail_log_bucket.bucket,
    include_global_service_events=True,
    is_multi_region_trail=True,
    enable_logging=True,
    opts=pulumi.ResourceOptions(depends_on=[cloudtrail_bucket_policy])
)







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
#pulumi.export("DevopsUser_mfa_arn", devops_user_mfa.arn)
pulumi.export("cloudtrail_name", cloudtrail.name)
pulumi.export("cloudtrail_log_bucket", cloudtrail_log_bucket.bucket)


pulumi.export("devops_deploy_arn", devops_deploy.arn)
pulumi.export("DevopsDeploy_mfa_arn", devops_deploy_mfa.arn)


pulumi.export("devops_automation_arn", devops_automation.arn)
pulumi.export("DevopsAutomation_mfa_arn", devops_automation_mfa.arn)

pulumi.export("devops_monitor_arn", devops_monitor.arn)
pulumi.export("DevopsMonitor_mfa_arn", devops_monitor_mfa.arn)

pulumi.export("devops_pipeline_arn", devops_pipeline.arn)
pulumi.export("DevopsPipeline_mfa_arn", devops_pipeline_mfa.arn)



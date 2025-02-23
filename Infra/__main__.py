"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws


config = pulumi.Config()
region = config.get("aws:region") or "us-east-1"



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

# # Setup MFA for DevopsUser
# devops_user_mfa = aws.iam.VirtualMfaDevice("DevopsUserMFA",
#     user=devops_user.name,
#     serial_number="arn:aws:iam::123456789012:mfa/DevopsUserVirtualMFA",
#     authentication_code1="123456",  # Replace with your MFA code part 1
#     authentication_code2="654321"   # Replace with your MFA code part 2
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
regular_buckets = [aws.s3.Bucket(f"company-data-Q{i}-2024") for i in range(1, 5)]
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
config_files_bucket = aws.s3.Bucket("configeration-files")
# ---------------------------------- #
# Create S3 bucket for Customer Data #
# ---------------------------------- #
customer_data_bucket = aws.s3.Bucket("customer-data")
# --------------------------------- #
# Create S3 bucket for Payment Data #
# --------------------------------- #
payment_data_bucket = aws.s3.Bucket("payment-data")







#   _____                                    _____  ____  
#  |  __ \                                  |  __ \|  _ \ 
#  | |  | |_   _ _ __   __ _ _ __ ___   ___ | |  | | |_) |
#  | |  | | | | | '_ \ / _` | '_ ` _ \ / _ \| |  | |  _ < 
#  | |__| | |_| | | | | (_| | | | | | | (_) | |__| | |_) |
#  |_____/ \__, |_| |_|\__,_|_| |_| |_|\___/|_____/|____/ 
#           __/ |                                         
#          |___/                                          

# Regular Orders Table (Non-Sensitive Information)
regular_table = aws.dynamodb.Table("customer_orders_table",
    name="CustomerOrdersTable",
    hash_key="ID",
    billing_mode="PAY_PER_REQUEST",
    attributes=[aws.dynamodb.TableAttributeArgs(
        name="ID",
        type="S"
    )]
)

# Sensitive Data Table (High-Value Target)
sensitive_table = aws.dynamodb.Table("customer_ssn_table",
    name="CustomerSSNTable",
    hash_key="ID",  # Only declare attributes that are used as keys
    billing_mode="PAY_PER_REQUEST",
    attributes=[aws.dynamodb.TableAttributeArgs(
        name="ID",
        type="S"
    )]
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
cloudtrail_log_bucket = aws.s3.Bucket("cloudtrail-log-bucket")
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
pulumi.export("regular_buckets", [bucket.bucket for bucket in regular_buckets])
pulumi.export("config_files_bucket", config_files_bucket.bucket)
pulumi.export("customer_data_bucket", customer_data_bucket.bucket)
pulumi.export("payment_data_bucket", payment_data_bucket.bucket)
pulumi.export("CustomerOrdersTable", regular_table.name)
pulumi.export("CustomerSSNTable", sensitive_table.name)
pulumi.export("gd_detector_id", gd_detector.id)
# pulumi.export("cloudtrail_id", cloudtrail.id)


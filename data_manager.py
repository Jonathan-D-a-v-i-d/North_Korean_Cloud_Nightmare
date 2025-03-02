import pulumi
import pulumi_aws as aws
import json
import random
from faker import Faker

#  Initialize Faker
fake = Faker()

#  Load Pulumi Stack Outputs
stack_outputs = pulumi.StackReference("dev")

config_bucket_id = stack_outputs.get_output("config_files_bucket")
customer_bucket_id = stack_outputs.get_output("customer_data_bucket")
payment_bucket_id = stack_outputs.get_output("payment_data_bucket")
orders_table_name = stack_outputs.get_output("CustomerOrdersTable")
ssn_table_name = stack_outputs.get_output("CustomerSSNTable")

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

#  Upload Data to S3 Using Pulumi
aws.s3.BucketObject("config-file",
    bucket=config_bucket_id,
    key="config.json",
    content=json.dumps(fake_config_data, indent=4)
)

aws.s3.BucketObject("customer-file",
    bucket=customer_bucket_id,
    key="customers.json",
    content=json.dumps(fake_customer_data, indent=4)
)

aws.s3.BucketObject("payment-file",
    bucket=payment_bucket_id,
    key="payments.json",
    content=json.dumps(fake_payment_data, indent=4)
)

#  Populate DynamoDB Tables Using Pulumi
for i in range(1, 101):
    aws.dynamodb.TableItem(f"order-{i}",
        table_name=orders_table_name,
        hash_key="ID",
        item=json.dumps({
            "ID": {"S": str(1000 + i)},
            "OrderDate": {"S": fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d")},
            "CustomerName": {"S": fake.name()},
            "ItemPurchased": {"S": random.choice(["Laptop", "Keyboard", "Monitor", "Mouse", "Tablet", "Phone", "Headphones", "Charger"])}
        })
    )

    aws.dynamodb.TableItem(f"ssn-{i}",
        table_name=ssn_table_name,
        hash_key="ID",
        item=json.dumps({
            "ID": {"S": str(2000 + i)},
            "CustomerName": {"S": fake.name()},
            "SSN": {"S": f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"},
            "CreditCard": {"S": f"{random.choice(['4111', '5500'])}-XXXX-XXXX-{random.randint(1000,9999)}"}
        })
    )

#  Export Data-Managed Objects
pulumi.export("config_file", "config.json")
pulumi.export("customer_file", "customers.json")
pulumi.export("payment_file", "payments.json")

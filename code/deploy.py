"""Task: provision three end-to-end AWS pipelines entirely using boto3."""
"""Task: End-points: API Gateway, Lambda and DynamoDB"""

import boto3, json, io, zipfile
from config import TLD_GROUPS, TABLE_SUFFIXES, ROUTES, METRIC_NAMESPACE

# References AWS Docs
# Students are asked to adapt the assignment requirement from these AWS examples
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/cross_service/apigateway_websocket_chat/README.md
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/dynamodb/GettingStarted/scenario_getting_started_movies.py
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/api-gateway/README.md

def create_tables(dynamodb, prefix):
    table_names = {}
    table_arns = {}
    for group, suffix in TABLE_SUFFIXES.items():
        table_name = f"{prefix}-{suffix}"
        table_names[group] = table_name
        try:
            dynamodb.describe_table(TableName=table_name)
            print(f"Using existing table: {table_name}")
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"Table needs to be created: {table_name}")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
        dynamodb.get_waiter("table_exists").wait(TableName=table_name)
        table_arns[group] = dynamodb.describe_table(TableName=table_name)["Table"]["TableArn"]
    return table_names, table_arns


def create_lambda_execution_role(iam, prefix, table_arns):
    role_name = f"{prefix}-homew2"
    trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
             }
        ]
    }
    response = ""
    try:
        response = iam.get_role(RoleName=role_name)
        print(f"Using existing role: {role_name}")
    except iam.exceptions.NoSuchEntityException:
        print(f"Role needs to be created: {role_name}")
        response = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
    role_arn = response["Role"]["Arn"]
    iam.attach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                ],
                "Resource": list(table_arns.values())
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cloudwatch:PutMetricData",
                ],
                "Resource": "*"
            }
        ]
    }
    iam.put_role_policy(RoleName=role_name, PolicyName=f"{prefix}-homew2-permissions", PolicyDocument=json.dumps(permissions_policy))
    return role_arn


def package_lambda_source_code():
    bytes_io = io.BytesIO()
    with zipfile.ZipFile(bytes_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write('lambda_function.py', arcname='lambda_function.py')
    return bytes_io.getvalue()


def create_lambdas(lambda_client, prefix, role_arn, zip_bytes, table_names):
    raise NotImplementedError


def create_http_api(apigatewayv2, lambda_client, prefix, function_arns):
    raise NotImplementedError


def create_dashboard(cloudwatch, prefix):
    raise NotImplementedError


def main():
    """Task: This must be end-to-end, and can not be manually created.Please do not create manually any of the above functions or feed into LLM to generate for you."""
    raise NotImplementedError


if __name__ == '__main__':
    main()

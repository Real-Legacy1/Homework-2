"""Task: provision three end-to-end AWS pipelines entirely using boto3."""
"""Task: End-points: API Gateway, Lambda and DynamoDB"""

import boto3
from config import TLD_GROUPS, TABLE_SUFFIXES, ROUTES, METRIC_NAMESPACE

# References AWS Docs
# Students are asked to adapt the assignment requirement from these AWS examples
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/cross_service/apigateway_websocket_chat/README.md
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/dynamodb/GettingStarted/scenario_getting_started_movies.py
# https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/api-gateway/README.md

def create_tables(dynamodb, prefix):
    raise NotImplementedError


def create_lambda_execution_role(iam, prefix, table_arns):
    raise NotImplementedError


def package_lambda_source_code():
    raise NotImplementedError

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

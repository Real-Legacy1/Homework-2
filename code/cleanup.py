# Task delete functionality for the resources used
import boto3
from config import PREFIX, REGION, TLD_GROUPS, TABLE_SUFFIXES

def delete_api(apigatewayv2,prefix):
    api_name = f"{prefix}-homew2-api"
    

def delete_lambda_function():
    raise NotImplementedError

def delete_lambda_execution_role():
    raise NotImplementedError

def delete_dynamo_db():
    raise NotImplementedError

def main():
    # TODO: delete API, Lambda functions, tables, dashboard, IAM role/policies and logs.
    raise NotImplementedError


if __name__ == '__main__':
    main()

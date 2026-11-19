"""Task: provision three end-to-end AWS pipelines entirely using boto3."""
"""Task: End-points: API Gateway, Lambda and DynamoDB"""

import boto3, json, io, zipfile, time

from config import TLD_GROUPS, TABLE_SUFFIXES, ROUTES, METRIC_NAMESPACE, PREFIX, REGION

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
    with zipfile.ZipFile(bytes_io, mode='w') as zipf:
        zipf.write('lambda_function.py', arcname='lambda_function.py')
    return bytes_io.getvalue()


def create_lambdas(lambda_client, prefix, role_arn, zip_bytes, table_names):
    table_arns = {}
    for group, table_name in table_names.items():
        lambda_name = f"{prefix}{group}Lambda"
        pipeline = group.lower()
        Variables = {
            "TABLE_NAME": table_name,
            "PIPELINE": pipeline,
            "METRIC_NAMESPACE": METRIC_NAMESPACE
        }
        try:
            response = lambda_client.get_function(FunctionName=lambda_name)
            print(f"Using existing Lambda function: {lambda_name}")
            response = lambda_client.update_function_code(FunctionName=lambda_name, ZipFile=zip_bytes)
            table_arns[group] = response["FunctionArn"]
        except lambda_client.exceptions.ResourceNotFoundException:
            
            print(f"Lambda function needs to be created: {lambda_name}")
            for attempt in range(10):
                try:
                    response = lambda_client.create_function(
                        FunctionName=lambda_name,
                        Runtime='python3.13',
                        Role=role_arn,
                        Handler='lambda_function.lambda_handler',
                        Code={'ZipFile': zip_bytes},
                        Environment={'Variables': Variables}
                    )
                    break;
                except lambda_client.exceptions.InvalidParameterValueException as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(5)
            lambda_client.get_waiter('function_active').wait(FunctionName=lambda_name)
            table_arns[group] = response['FunctionArn']
    
    return table_arns
    


def create_http_api(apigatewayv2, lambda_client, prefix, function_arns):
    api_name = f"{prefix}-homew2-api"

    response = apigatewayv2.get_apis()
    api_id = None
    for api in response['Items']:
        if api['Name'] == api_name:
            api_id = api['ApiId']
            apiendpoint = api['ApiEndpoint']
            break
    if api_id:
        print(f"Using existing API: {api_name}")
    else:
        print(f"API needs to be created: {api_name}")
        response = apigatewayv2.create_api(Name=api_name, ProtocolType='HTTP')
        api_id = response['ApiId']
        apiendpoint = response['ApiEndpoint']
    routes = apigatewayv2.get_routes(ApiId=api_id)
    route_ids = {}
    for route in routes['Items']:
        route_ids[route['RouteKey']] = route['RouteId']
    for group, function_arn in function_arns.items():
        route_key = ROUTES[group]
        if route_key in route_ids:
            print(f"Using existing route: {route_key}")
        else:
            create_integration_response = apigatewayv2.create_integration(
                ApiId=api_id,
                IntegrationType='AWS_PROXY',
                IntegrationUri=function_arn,
                PayloadFormatVersion='2.0'
            )
            apigatewayv2.create_route(ApiId=api_id, RouteKey=route_key, Target=f'integrations/{create_integration_response["IntegrationId"]}')
        source_arn = f'arn:aws:execute-api:{apigatewayv2.meta.region_name}:{boto3.client("sts").get_caller_identity()["Account"]}:{api_id}/*/*'
        try:
            lambda_client.add_permission(
                FunctionName=function_arn,
                StatementId=f'{prefix}-{group}-permission',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
        except lambda_client.exceptions.ResourceConflictException:
            print(f"Permission already exists for {function_arn} to be invoked by API Gateway.")
    try:
        apigatewayv2.create_stage(ApiId=api_id, StageName='$default', AutoDeploy=True)
    except apigatewayv2.exceptions.ConflictException:
        print(f"stage already exists for API: {api_name}")
    return apiendpoint

    
        
        




def create_dashboard(cloudwatch, prefix):
    dashboard_name = f"{prefix}-homew2-dashboard"
    try:
        cloudwatch.get_dashboard(DashboardName=dashboard_name)
        print(f"Using existing dashboard: {dashboard_name}")
    except cloudwatch.exceptions.DashboardNotFoundError:
        print(f"Dashboard needs to be created: {dashboard_name}")
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "generic", "TLD", "com"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "generic", "TLD", "org"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "generic", "TLD", "net"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "country", "TLD", "us"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "country", "TLD", "uk"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "country", "TLD", "de"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "country", "TLD", "np"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "selected", "TLD", "xyz"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "selected", "TLD", "top"],
                            [METRIC_NAMESPACE, "IngestedCount", "Pipeline", "selected", "TLD", "shop"]

                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": cloudwatch.meta.region_name,
                        "title": "Pipeline Metrics"
                    }
                }
            ]
        }
        cloudwatch.put_dashboard(DashboardName=dashboard_name, DashboardBody=json.dumps(dashboard_body))
    return dashboard_name

def main():
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    lambda_client = boto3.client("lambda", region_name=REGION)
    apigatewayv2 = boto3.client("apigatewayv2", region_name=REGION)
    table_names, table_arns = create_tables(dynamodb, PREFIX)
    role_arn = create_lambda_execution_role(iam, PREFIX, table_arns)
    package = package_lambda_source_code()
    lambdas = create_lambdas(lambda_client, PREFIX, role_arn, package, table_names)
    httpapi = create_http_api(apigatewayv2, lambda_client, PREFIX, lambdas)
    dashboard = create_dashboard(cloudwatch, PREFIX)
    print(f"API endpoint: {httpapi}")
    print(f"Dashboard created: {dashboard}")
    with open("api_endpoint.txt", "w") as f:
        f.write(httpapi)
    

if __name__ == '__main__':
    main()

"""Task: Deploy Lambda three times with different PIPELINE (TLD types)"""
import json
import os
import uuid
from datetime import datetime, timezone
import boto3


def lambda_handler(event, context):
    """Task:
    - Parse event['body'] as JSON; return 400 for invalid JSON or missing required fields.
    - Validate TLD against and return if any found unsupported TLDs
    - Insert data to DynamoDB via PutItem
    - Add logts to CloudWatch metric with Pipeline and TLD dimensions
    - On error log failure, emit ErrorCount metric and return 5xx 
    - Return JSON body with HTTP 200 upon success or related error code
    """
    body = event.get('body')
    try:
        body = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid request body"})
        }
    if not isinstance(body, dict):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Request body must be a JSON object"})
        }
    required_fields = [
    "url",
    "tld",
    "second_level_domain",
    "third_level_domain",
    "path",
    ]
    for field in required_fields:
        if field not in body:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Missing required field: {field}"})
            }
    generic_tlds = {'com', 'net', 'org'}
    country_tlds = {'us', 'uk', 'de', 'np'}
    selected_tlds = {'xyz', 'top', 'shop'}
    tld = body.get('tld')
    if not isinstance(tld, str):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "TLD must be a string"})
        }
    tld_group = None
    if tld in generic_tlds:
        tld_group = "generic"
    elif tld in country_tlds:
        tld_group = "country"
    elif tld in selected_tlds:
        tld_group = "selected"
    if tld_group is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unsupported TLD: {tld}"})
        }
    pipeline = os.environ["PIPELINE"]
    if tld_group != pipeline:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"TLD group {tld_group} does not match pipeline {pipeline}"})
        }
    ingested_at = datetime.now(timezone.utc).isoformat()
    item = body.copy()
    item["id"] = str(uuid.uuid4())
    item["ingested_at"] = ingested_at
    item["pipeline"]= pipeline
    table_name = os.environ["TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    cloudwatch = boto3.client("cloudwatch")
    namespace = os.environ.get("METRIC_NAMESPACE", "Coursework/PhishingTLDTracker")

    table = dynamodb.Table(table_name)
    try:
        table.put_item(Item=item)
    except Exception as e:
        print(f"Error inserting item into DynamoDB: {e}")
        try:
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        "MetricName": "ErrorCount",
                        "Dimensions": [
                            {"Name": "Pipeline", "Value": pipeline},
                            {"Name": "TLD", "Value": tld}
                        ],
                        "Value": 1,
                        "Unit": "Count"
                    }
                ]
            )
        except Exception as ce:
            print(f"Error emitting CloudWatch metric: {ce}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
    
    metricName = "IngestedCount"
    try:
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": metricName,
                    "Dimensions": [
                        {"Name": "Pipeline", "Value": pipeline},
                        {"Name": "TLD", "Value": tld}
                    ],
                    "Value": 1,
                    "Unit": "Count"
                }
            ]
        )
    except Exception as ce:
        print(f"Error emitting CloudWatch metric: {ce}")
    return {
            "statusCode": 200,
            "body": json.dumps({"message": "Record ingested successfully"})     
        }   

    
    
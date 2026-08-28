import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

BACKEND_ROOT = Path(__file__).parent.parent
LAYER_PATH = BACKEND_ROOT / "src" / "layers" / "common" / "python"

# Make `common.*` importable, same as it would be at /opt/python inside Lambda
sys.path.insert(0, str(LAYER_PATH))

# Make each function importable as a package, e.g. `presign_upload.app`
sys.path.insert(0, str(BACKEND_ROOT / "src"))


@pytest.fixture
def aws_env(monkeypatch):
    """Fake AWS credentials/region so boto3 never tries to hit real AWS."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mocked_aws(aws_env, monkeypatch):
    """Spin up mocked DynamoDB table + S3 bucket in a single moto context,
    matching our real schema/bucket. Use this fixture whenever a test needs
    either or both."""
    monkeypatch.setenv("TABLE_NAME", "receipts-table-test")
    monkeypatch.setenv("BUCKET_NAME", "receipt-tracker-images-test")
    with mock_aws():
        dynamo_client = boto3.client("dynamodb", region_name="us-east-1")
        dynamo_client.create_table(
            TableName="receipts-table-test",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="receipt-tracker-images-test")

        yield

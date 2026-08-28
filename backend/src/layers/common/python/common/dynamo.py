import os
import boto3

_dynamodb = boto3.resource("dynamodb")


def get_table():
    """Return the DynamoDB Table resource, reading the name from env vars.

    Reading the table name at call time (not import time) makes this
    easy to mock in tests with moto + monkeypatched env vars.
    """
    table_name = os.environ["TABLE_NAME"]
    return _dynamodb.Table(table_name)


def receipt_pk(user_id: str) -> str:
    return f"USER#{user_id}"


def receipt_sk(receipt_id: str) -> str:
    return f"RECEIPT#{receipt_id}"

import os
import boto3

from common.responses import ok, unauthorized, bad_request, not_found, server_error
from common.dynamo import get_table, receipt_pk, receipt_sk
from common.auth import get_user_id

s3 = boto3.client("s3")


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    receipt_id = (event.get("pathParameters") or {}).get("receiptId")
    if not receipt_id:
        return bad_request("Missing receiptId in path")

    try:
        table = get_table()

        # Query for the main record + all its line items, so we delete
        # everything belonging to this receipt, not just the parent row.
        result = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": receipt_pk(user_id),
                ":sk_prefix": receipt_sk(receipt_id),
            },
        )
        items = result.get("Items", [])
        if not items:
            return not_found("Receipt not found")

        main_record = next((i for i in items if "#ITEM#" not in i["SK"]), None)

        # Delete every DynamoDB row for this receipt (main record + line items).
        # batch_writer() automatically groups deletes into efficient batch
        # requests instead of one round trip per item.
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        # Also delete the underlying image from S3, so storage doesn't leak
        s3_key = main_record.get("s3Key") if main_record else None
        if s3_key:
            bucket_name = os.environ["BUCKET_NAME"]
            s3.delete_object(Bucket=bucket_name, Key=s3_key)

        return ok({"receiptId": receipt_id, "deleted": True})
    except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
        print(f"Error deleting receipt {receipt_id} for user {user_id}: {exc}")
        return server_error("Could not delete receipt")

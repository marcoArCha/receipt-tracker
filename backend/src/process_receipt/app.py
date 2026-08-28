import os
import urllib.parse
import boto3

from common.dynamo import get_table, receipt_pk, receipt_sk
from common.textract_parser import parse_expense_response

textract = boto3.client("textract")


def _parse_s3_key(key: str):
    """Extract userId and receiptId from a key like receipts/{userId}/{receiptId}.jpg"""
    parts = key.split("/")
    if len(parts) != 3 or parts[0] != "receipts":
        return None, None
    user_id = parts[1]
    receipt_id = parts[2].rsplit(".", 1)[0]
    return user_id, receipt_id


def _mark_failed(table, user_id: str, receipt_id: str, reason: str):
    table.update_item(
        Key={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id)},
        UpdateExpression="SET #s = :status, failureReason = :reason",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": "FAILED", ":reason": reason},
    )


def lambda_handler(event, context):
    table = get_table()

    for record in event.get("Records", []):
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        user_id, receipt_id = _parse_s3_key(object_key)
        if not user_id or not receipt_id:
            print(f"Skipping unrecognized key format: {object_key}")
            continue

        try:
            response = textract.analyze_expense(
                Document={
                    "S3Object": {"Bucket": bucket_name, "Name": object_key}
                }
            )
            parsed = parse_expense_response(response)

            # Update the main receipt record with extracted summary fields
            table.update_item(
                Key={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id)},
                UpdateExpression=(
                    "SET #s = :status, merchant = :merchant, "
                    "receiptDate = :date, #t = :total"
                ),
                ExpressionAttributeNames={"#s": "status", "#t": "total"},
                ExpressionAttributeValues={
                    ":status": "PROCESSED",
                    ":merchant": parsed["merchant"],
                    ":date": parsed["date"],
                    ":total": parsed["total"],
                },
            )

            # Write each line item as its own row under the same partition
            for index, item in enumerate(parsed["items"]):
                table.put_item(
                    Item={
                        "PK": receipt_pk(user_id),
                        "SK": f"{receipt_sk(receipt_id)}#ITEM#{index}",
                        "receiptId": receipt_id,
                        "name": item["name"],
                        "price": item["price"],
                        "quantity": item["quantity"],
                    }
                )

        except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
            print(f"Error processing receipt {object_key}: {exc}")
            _mark_failed(table, user_id, receipt_id, str(exc))

    return {"statusCode": 200}

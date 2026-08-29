import json
import os
import uuid
import time
import boto3

from common.responses import ok, unauthorized, bad_request, server_error
from common.dynamo import get_table, receipt_pk, receipt_sk
from common.auth import get_user_id

s3 = boto3.client("s3")

# Only these content types are accepted - both for security (don't let
# someone presign a URL for arbitrary file types via this endpoint) and
# because Textract's AnalyzeExpense only supports these image formats.
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return bad_request("Invalid JSON body")

    # Default to jpeg if the client doesn't specify one, for convenience
    content_type = body.get("contentType", "image/jpeg")
    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if not extension:
        return bad_request(
            f"Unsupported contentType '{content_type}'. "
            f"Allowed: {list(ALLOWED_CONTENT_TYPES.keys())}"
        )

    try:
        bucket_name = os.environ["BUCKET_NAME"]
        receipt_id = str(uuid.uuid4())
        s3_key = f"receipts/{user_id}/{receipt_id}.{extension}"

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=300,  # URL valid for 5 minutes
        )

        table = get_table()
        table.put_item(
            Item={
                "PK": receipt_pk(user_id),
                "SK": receipt_sk(receipt_id),
                "receiptId": receipt_id,
                "status": "PENDING",
                "s3Key": s3_key,
                "createdAt": int(time.time()),
            }
        )

        return ok(
            {
                "receiptId": receipt_id,
                "uploadUrl": upload_url,
                "s3Key": s3_key,
            }
        )
    except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
        print(f"Error generating presigned upload: {exc}")
        return server_error("Could not generate upload URL")

import os
import uuid
import time
import boto3

from common.responses import ok, unauthorized, server_error
from common.dynamo import get_table, receipt_pk, receipt_sk
from common.auth import get_user_id

s3 = boto3.client("s3")


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    try:
        bucket_name = os.environ["BUCKET_NAME"]
        receipt_id = str(uuid.uuid4())
        s3_key = f"receipts/{user_id}/{receipt_id}.jpg"

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "ContentType": "image/jpeg",
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

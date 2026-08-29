def _event(user_id, receipt_id):
    return {
        "requestContext": {"authorizer": {"claims": {"sub": user_id}}},
        "pathParameters": {"receiptId": receipt_id},
    }


def test_returns_401_when_no_user_id(mocked_aws):
    from delete_receipt.app import lambda_handler

    response = lambda_handler({"pathParameters": {"receiptId": "r1"}}, context=None)

    assert response["statusCode"] == 401


def test_returns_404_for_nonexistent_receipt(mocked_aws):
    from delete_receipt.app import lambda_handler

    response = lambda_handler(_event("user-1", "does-not-exist"), context=None)

    assert response["statusCode"] == 404


def test_deletes_receipt_and_line_items_and_s3_object(mocked_aws):
    from delete_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk
    import boto3

    user_id, receipt_id = "user-1", "r1"
    s3_key = f"receipts/{user_id}/{receipt_id}.jpg"

    table = get_table()
    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": receipt_sk(receipt_id),
            "receiptId": receipt_id,
            "s3Key": s3_key,
        }
    )
    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": f"{receipt_sk(receipt_id)}#ITEM#0",
            "name": "Coffee",
        }
    )

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.put_object(
        Bucket="receipt-tracker-images-test", Key=s3_key, Body=b"fake-image-bytes"
    )

    response = lambda_handler(_event(user_id, receipt_id), context=None)
    assert response["statusCode"] == 200

    # DynamoDB rows gone
    result = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
        ExpressionAttributeValues={
            ":pk": receipt_pk(user_id),
            ":sk": receipt_sk(receipt_id),
        },
    )
    assert result["Items"] == []

    # S3 object gone
    listing = s3_client.list_objects_v2(
        Bucket="receipt-tracker-images-test", Prefix=s3_key
    )
    assert listing.get("KeyCount", 0) == 0


def test_cannot_delete_another_users_receipt(mocked_aws):
    from delete_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    table = get_table()
    table.put_item(
        Item={"PK": receipt_pk("user-1"), "SK": receipt_sk("r1"), "receiptId": "r1"}
    )

    response = lambda_handler(_event("user-2", "r1"), context=None)
    assert response["statusCode"] == 404

    # Confirm it's untouched
    item = table.get_item(
        Key={"PK": receipt_pk("user-1"), "SK": receipt_sk("r1")}
    ).get("Item")
    assert item is not None

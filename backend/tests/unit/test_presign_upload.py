import json


def _make_event(user_id: str | None):
    """Build a fake API Gateway event, mimicking what API Gateway sends
    once the Cognito Authorizer has verified the request."""
    event = {"requestContext": {}}
    if user_id:
        event["requestContext"]["authorizer"] = {"claims": {"sub": user_id}}
    return event


def test_returns_401_when_no_user_id(mocked_aws):
    from presign_upload.app import lambda_handler

    response = lambda_handler(_make_event(user_id=None), context=None)

    assert response["statusCode"] == 401


def test_generates_upload_url_and_creates_pending_record(mocked_aws):
    from presign_upload.app import lambda_handler
    from common.dynamo import get_table, receipt_pk

    user_id = "test-user-123"
    response = lambda_handler(_make_event(user_id=user_id), context=None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])

    # Response contains what the frontend needs to upload directly to S3
    assert "receiptId" in body
    assert body["uploadUrl"].startswith("https://")
    assert user_id in body["s3Key"]
    assert body["s3Key"].endswith(".jpg")

    # A PENDING record should now exist in DynamoDB for this user
    table = get_table()
    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": receipt_pk(user_id)},
    )
    items = result["Items"]
    assert len(items) == 1
    assert items[0]["status"] == "PENDING"
    assert items[0]["receiptId"] == body["receiptId"]


def test_each_call_generates_a_unique_receipt_id(mocked_aws):
    from presign_upload.app import lambda_handler

    user_id = "test-user-456"
    response_1 = lambda_handler(_make_event(user_id), context=None)
    response_2 = lambda_handler(_make_event(user_id), context=None)

    body_1 = json.loads(response_1["body"])
    body_2 = json.loads(response_2["body"])

    assert body_1["receiptId"] != body_2["receiptId"]

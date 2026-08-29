import json


def _make_event(user_id: str | None, receipt_id: str | None):
    event = {"requestContext": {}, "pathParameters": {}}
    if user_id:
        event["requestContext"]["authorizer"] = {"claims": {"sub": user_id}}
    if receipt_id:
        event["pathParameters"]["receiptId"] = receipt_id
    return event


def test_returns_401_when_no_user_id(mocked_aws):
    from get_receipt.app import lambda_handler

    response = lambda_handler(_make_event(None, "r1"), context=None)
    assert response["statusCode"] == 401


def test_returns_400_when_no_receipt_id(mocked_aws):
    from get_receipt.app import lambda_handler

    response = lambda_handler(_make_event("user-1", None), context=None)
    assert response["statusCode"] == 400


def test_returns_404_when_receipt_does_not_exist(mocked_aws):
    from get_receipt.app import lambda_handler

    response = lambda_handler(_make_event("user-1", "does-not-exist"), context=None)
    assert response["statusCode"] == 404


def test_returns_receipt_with_line_items(mocked_aws):
    from get_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    user_id = "user-1"
    receipt_id = "r1"
    table = get_table()
    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": receipt_sk(receipt_id),
            "receiptId": receipt_id,
            "status": "PROCESSED",
            "merchant": "Cafe Britt",
            "total": "12.50",
            "s3Key": f"receipts/{user_id}/{receipt_id}.jpg",
        }
    )
    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": f"{receipt_sk(receipt_id)}#ITEM#0",
            "receiptId": receipt_id,
            "name": "Coffee",
            "price": "12.50",
            "quantity": "1",
        }
    )

    response = lambda_handler(_make_event(user_id, receipt_id), context=None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["merchant"] == "Cafe Britt"
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Coffee"


def test_cannot_access_another_users_receipt(mocked_aws):
    """A user's PK is derived from their own Cognito id, so even knowing
    another user's receiptId shouldn't return that receipt."""
    from get_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    table = get_table()
    table.put_item(
        Item={
            "PK": receipt_pk("owner-user"),
            "SK": receipt_sk("shared-receipt-id"),
            "receiptId": "shared-receipt-id",
            "status": "PROCESSED",
        }
    )

    response = lambda_handler(_make_event("attacker-user", "shared-receipt-id"), context=None)
    assert response["statusCode"] == 404

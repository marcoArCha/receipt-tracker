import json


def _event(user_id, receipt_id, body):
    return {
        "requestContext": {"authorizer": {"claims": {"sub": user_id}}},
        "pathParameters": {"receiptId": receipt_id},
        "body": json.dumps(body),
    }


def _seed_receipt(table, user_id, receipt_id, **extra):
    from common.dynamo import receipt_pk, receipt_sk

    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": receipt_sk(receipt_id),
            "receiptId": receipt_id,
            "status": "PROCESSED",
            **extra,
        }
    )


def test_returns_401_when_no_user_id(mocked_aws):
    from update_receipt.app import lambda_handler

    event = {"pathParameters": {"receiptId": "r1"}, "body": "{}"}
    response = lambda_handler(event, context=None)

    assert response["statusCode"] == 401


def test_returns_400_when_no_valid_fields(mocked_aws):
    from update_receipt.app import lambda_handler
    from common.dynamo import get_table

    _seed_receipt(get_table(), "user-1", "r1")
    response = lambda_handler(
        _event("user-1", "r1", {"status": "PROCESSED"}), context=None
    )

    assert response["statusCode"] == 400


def test_returns_404_for_nonexistent_receipt(mocked_aws):
    from update_receipt.app import lambda_handler

    response = lambda_handler(
        _event("user-1", "does-not-exist", {"merchant": "Corrected Store"}),
        context=None,
    )

    assert response["statusCode"] == 404


def test_updates_allowed_fields(mocked_aws):
    from update_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    table = get_table()
    _seed_receipt(table, "user-1", "r1", merchant="Wrong Name", total="0.00")

    response = lambda_handler(
        _event("user-1", "r1", {"merchant": "Corrected Store", "total": "15.00"}),
        context=None,
    )

    assert response["statusCode"] == 200

    item = table.get_item(
        Key={"PK": receipt_pk("user-1"), "SK": receipt_sk("r1")}
    )["Item"]
    assert item["merchant"] == "Corrected Store"
    assert item["total"] == "15.00"


def test_cannot_update_another_users_receipt(mocked_aws):
    from update_receipt.app import lambda_handler
    from common.dynamo import get_table

    _seed_receipt(get_table(), "user-1", "r1", merchant="Original")

    response = lambda_handler(
        _event("user-2", "r1", {"merchant": "Hijacked"}), context=None
    )

    assert response["statusCode"] == 404

def _make_event(user_id: str | None):
    event = {"requestContext": {}}
    if user_id:
        event["requestContext"]["authorizer"] = {"claims": {"sub": user_id}}
    return event


def _seed_receipt(table, user_id, receipt_id, status="PROCESSED", merchant=None,
                   total=None, created_at=1000):
    from common.dynamo import receipt_pk, receipt_sk

    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": receipt_sk(receipt_id),
            "receiptId": receipt_id,
            "status": status,
            "merchant": merchant,
            "total": total,
            "createdAt": created_at,
        }
    )


def _seed_line_item(table, user_id, receipt_id, index, name):
    from common.dynamo import receipt_pk, receipt_sk

    table.put_item(
        Item={
            "PK": receipt_pk(user_id),
            "SK": f"{receipt_sk(receipt_id)}#ITEM#{index}",
            "receiptId": receipt_id,
            "name": name,
        }
    )


def test_returns_401_when_no_user_id(mocked_aws):
    from get_receipts.app import lambda_handler

    response = lambda_handler(_make_event(user_id=None), context=None)
    assert response["statusCode"] == 401


def test_returns_empty_list_for_new_user(mocked_aws):
    from get_receipts.app import lambda_handler
    import json

    response = lambda_handler(_make_event("new-user"), context=None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["receipts"] == []


def test_lists_receipts_excluding_line_items(mocked_aws):
    from get_receipts.app import lambda_handler
    from common.dynamo import get_table
    import json

    table = get_table()
    user_id = "user-1"
    _seed_receipt(table, user_id, "r1", merchant="Cafe Britt", total="12.50", created_at=2000)
    _seed_receipt(table, user_id, "r2", status="PENDING", created_at=1000)
    _seed_line_item(table, user_id, "r1", 0, "Coffee")

    response = lambda_handler(_make_event(user_id), context=None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert len(body["receipts"]) == 2  # line item must NOT be included

    # Most recent first
    assert body["receipts"][0]["receiptId"] == "r1"
    assert body["receipts"][0]["merchant"] == "Cafe Britt"
    assert body["receipts"][1]["receiptId"] == "r2"
    assert body["receipts"][1]["status"] == "PENDING"


def test_only_returns_the_requesting_users_receipts(mocked_aws):
    from get_receipts.app import lambda_handler
    from common.dynamo import get_table
    import json

    table = get_table()
    _seed_receipt(table, "user-a", "r1", merchant="Store A")
    _seed_receipt(table, "user-b", "r2", merchant="Store B")

    response = lambda_handler(_make_event("user-a"), context=None)
    body = json.loads(response["body"])

    assert len(body["receipts"]) == 1
    assert body["receipts"][0]["merchant"] == "Store A"

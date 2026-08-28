from unittest.mock import patch


def _s3_event(bucket: str, key: str) -> dict:
    """Build a fake S3 ObjectCreated event, matching what S3 actually sends."""
    return {
        "Records": [
            {"s3": {"bucket": {"name": bucket}, "object": {"key": key}}}
        ]
    }


def _fake_textract_response():
    return {
        "ExpenseDocuments": [
            {
                "SummaryFields": [
                    {"Type": {"Text": "VENDOR_NAME"}, "ValueDetection": {"Text": "Cafe Britt"}},
                    {"Type": {"Text": "TOTAL"}, "ValueDetection": {"Text": "12.50"}},
                ],
                "LineItemGroups": [
                    {
                        "LineItems": [
                            {
                                "LineItemExpenseFields": [
                                    {"Type": {"Text": "ITEM"}, "ValueDetection": {"Text": "Coffee"}},
                                    {"Type": {"Text": "PRICE"}, "ValueDetection": {"Text": "12.50"}},
                                ]
                            }
                        ]
                    }
                ],
            }
        ]
    }


def test_processes_receipt_and_updates_dynamo(mocked_aws):
    from process_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    user_id = "user-1"
    receipt_id = "receipt-1"
    key = f"receipts/{user_id}/{receipt_id}.jpg"

    table = get_table()
    table.put_item(
        Item={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id), "status": "PENDING"}
    )

    with patch("process_receipt.app.textract") as mock_textract:
        mock_textract.analyze_expense.return_value = _fake_textract_response()
        event = _s3_event("receipt-tracker-images-test", key)
        response = lambda_handler(event, context=None)

    assert response["statusCode"] == 200

    result = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": receipt_pk(user_id)},
    )
    items = {i["SK"]: i for i in result["Items"]}

    main_record = items[receipt_sk(receipt_id)]
    assert main_record["status"] == "PROCESSED"
    assert main_record["merchant"] == "Cafe Britt"
    assert main_record["total"] == "12.50"

    line_item_keys = [k for k in items if "#ITEM#" in k]
    assert len(line_item_keys) == 1
    assert items[line_item_keys[0]]["name"] == "Coffee"


def test_marks_receipt_failed_when_textract_errors(mocked_aws):
    from process_receipt.app import lambda_handler
    from common.dynamo import get_table, receipt_pk, receipt_sk

    user_id = "user-2"
    receipt_id = "receipt-2"
    key = f"receipts/{user_id}/{receipt_id}.jpg"

    table = get_table()
    table.put_item(
        Item={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id), "status": "PENDING"}
    )

    with patch("process_receipt.app.textract") as mock_textract:
        mock_textract.analyze_expense.side_effect = Exception("Textract blew up")
        event = _s3_event("receipt-tracker-images-test", key)
        lambda_handler(event, context=None)

    result = table.get_item(Key={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id)})
    assert result["Item"]["status"] == "FAILED"
    assert "Textract blew up" in result["Item"]["failureReason"]


def test_skips_records_with_unrecognized_key_format(mocked_aws):
    from process_receipt.app import lambda_handler

    with patch("process_receipt.app.textract") as mock_textract:
        event = _s3_event("receipt-tracker-images-test", "some/other/path.jpg")
        response = lambda_handler(event, context=None)

    mock_textract.analyze_expense.assert_not_called()
    assert response["statusCode"] == 200

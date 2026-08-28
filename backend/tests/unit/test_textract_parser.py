from common.textract_parser import parse_expense_response


def _field(field_type: str, text: str) -> dict:
    return {"Type": {"Text": field_type}, "ValueDetection": {"Text": text}}


def test_returns_empty_result_when_no_documents():
    result = parse_expense_response({"ExpenseDocuments": []})
    assert result == {"merchant": None, "date": None, "total": None, "items": []}


def test_extracts_summary_fields():
    response = {
        "ExpenseDocuments": [
            {
                "SummaryFields": [
                    _field("VENDOR_NAME", "Trader Joe's"),
                    _field("INVOICE_RECEIPT_DATE", "2026-08-20"),
                    _field("TOTAL", "42.17"),
                ],
                "LineItemGroups": [],
            }
        ]
    }

    result = parse_expense_response(response)

    assert result["merchant"] == "Trader Joe's"
    assert result["date"] == "2026-08-20"
    assert result["total"] == "42.17"
    assert result["items"] == []


def test_extracts_line_items():
    response = {
        "ExpenseDocuments": [
            {
                "SummaryFields": [],
                "LineItemGroups": [
                    {
                        "LineItems": [
                            {
                                "LineItemExpenseFields": [
                                    _field("ITEM", "Bananas"),
                                    _field("PRICE", "1.99"),
                                    _field("QUANTITY", "1"),
                                ]
                            },
                            {
                                "LineItemExpenseFields": [
                                    _field("ITEM", "Oat milk"),
                                    _field("PRICE", "4.50"),
                                    _field("QUANTITY", "2"),
                                ]
                            },
                        ]
                    }
                ],
            }
        ]
    }

    result = parse_expense_response(response)

    assert len(result["items"]) == 2
    assert result["items"][0] == {"name": "Bananas", "price": "1.99", "quantity": "1"}
    assert result["items"][1] == {"name": "Oat milk", "price": "4.50", "quantity": "2"}


def test_skips_line_items_with_no_name():
    """A malformed/low-confidence Textract line item shouldn't crash parsing,
    it should just be excluded since it's not usable data."""
    response = {
        "ExpenseDocuments": [
            {
                "SummaryFields": [],
                "LineItemGroups": [
                    {"LineItems": [{"LineItemExpenseFields": [_field("PRICE", "3.00")]}]}
                ],
            }
        ]
    }

    result = parse_expense_response(response)

    assert result["items"] == []

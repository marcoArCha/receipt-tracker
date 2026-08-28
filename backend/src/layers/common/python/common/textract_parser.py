def parse_expense_response(textract_response: dict) -> dict:
    """Convert a Textract AnalyzeExpense response into a simple dict:
        {
            "merchant": str | None,
            "date": str | None,
            "total": str | None,
            "items": [{"name": str, "price": str | None, "quantity": str | None}, ...]
        }

    Textract's raw response is deeply nested and verbose, so we isolate
    that parsing logic here, separate from AWS calls, which makes it easy
    to unit test with plain Python dicts (no mocking needed for this part).
    """
    result = {"merchant": None, "date": None, "total": None, "items": []}

    documents = textract_response.get("ExpenseDocuments", [])
    if not documents:
        return result

    doc = documents[0]

    # Summary fields (merchant, date, total) live in "SummaryFields"
    field_map = {
        "VENDOR_NAME": "merchant",
        "INVOICE_RECEIPT_DATE": "date",
        "TOTAL": "total",
    }
    for field in doc.get("SummaryFields", []):
        field_type = field.get("Type", {}).get("Text")
        our_key = field_map.get(field_type)
        if our_key:
            value = field.get("ValueDetection", {}).get("Text")
            if value:
                result[our_key] = value

    # Line items live in "LineItemGroups" -> "LineItems" -> "LineItemExpenseFields"
    item_field_map = {
        "ITEM": "name",
        "PRICE": "price",
        "QUANTITY": "quantity",
    }
    for group in doc.get("LineItemGroups", []):
        for line_item in group.get("LineItems", []):
            parsed_item = {"name": None, "price": None, "quantity": None}
            for field in line_item.get("LineItemExpenseFields", []):
                field_type = field.get("Type", {}).get("Text")
                our_key = item_field_map.get(field_type)
                if our_key:
                    parsed_item[our_key] = field.get("ValueDetection", {}).get("Text")
            if parsed_item["name"]:
                result["items"].append(parsed_item)

    return result

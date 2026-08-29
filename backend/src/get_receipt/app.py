from common.responses import ok, unauthorized, not_found, bad_request, server_error
from common.dynamo import get_table, receipt_pk, receipt_sk
from common.auth import get_user_id


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    receipt_id = (event.get("pathParameters") or {}).get("receiptId")
    if not receipt_id:
        return bad_request("Missing receiptId in path")

    try:
        table = get_table()
        # A single query returns the main receipt record AND all of its
        # line items, since they share the same PK and their SKs both
        # start with the same RECEIPT#<id> prefix.
        result = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": receipt_pk(user_id),
                ":sk_prefix": receipt_sk(receipt_id),
            },
        )

        items = result.get("Items", [])
        if not items:
            return not_found("Receipt not found")

        main_record = next((i for i in items if "#ITEM#" not in i["SK"]), None)
        if not main_record:
            return not_found("Receipt not found")

        line_items = [
            {
                "name": i.get("name"),
                "price": i.get("price"),
                "quantity": i.get("quantity"),
            }
            for i in items
            if "#ITEM#" in i["SK"]
        ]

        return ok(
            {
                "receiptId": main_record.get("receiptId"),
                "status": main_record.get("status"),
                "merchant": main_record.get("merchant"),
                "total": main_record.get("total"),
                "date": main_record.get("receiptDate"),
                "s3Key": main_record.get("s3Key"),
                "failureReason": main_record.get("failureReason"),
                "items": line_items,
            }
        )
    except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
        print(f"Error getting receipt {receipt_id} for user {user_id}: {exc}")
        return server_error("Could not get receipt")
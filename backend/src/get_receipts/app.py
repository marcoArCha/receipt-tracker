from common.responses import ok, unauthorized, server_error
from common.dynamo import get_table, receipt_pk
from common.auth import get_user_id


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    try:
        table = get_table()
        result = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            FilterExpression="NOT contains(SK, :item_marker)",
            ExpressionAttributeValues={
                ":pk": receipt_pk(user_id),
                ":sk_prefix": "RECEIPT#",
                ":item_marker": "#ITEM#",
            },
        )

        receipts = [
            {
                "receiptId": item.get("receiptId"),
                "status": item.get("status"),
                "merchant": item.get("merchant"),
                "total": item.get("total"),
                "date": item.get("receiptDate"),
                "createdAt": item.get("createdAt"),
            }
            for item in result.get("Items", [])
        ]

        # Most recent first
        receipts.sort(key=lambda r: r["createdAt"] or 0, reverse=True)

        return ok({"receipts": receipts})
    except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
        print(f"Error listing receipts for user {user_id}: {exc}")
        return server_error("Could not list receipts")

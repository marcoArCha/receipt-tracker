import json

from common.responses import ok, unauthorized, bad_request, not_found, server_error
from common.dynamo import get_table, receipt_pk, receipt_sk
from common.auth import get_user_id

# Fields a user is allowed to correct. Deliberately explicit/whitelisted -
# we never want a client to be able to overwrite things like `status` or
# `s3Key` through this endpoint.
EDITABLE_FIELDS = {
    "merchant": "merchant",
    "total": "total",
    "date": "receiptDate",
}


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return unauthorized("Missing or invalid user identity")

    receipt_id = (event.get("pathParameters") or {}).get("receiptId")
    if not receipt_id:
        return bad_request("Missing receiptId in path")

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return bad_request("Invalid JSON body")

    updates = {
        EDITABLE_FIELDS[key]: value
        for key, value in body.items()
        if key in EDITABLE_FIELDS
    }
    if not updates:
        return bad_request(
            f"No valid fields to update. Allowed: {list(EDITABLE_FIELDS.keys())}"
        )

    try:
        table = get_table()

        # Confirm the receipt exists and belongs to this user before writing.
        existing = table.get_item(
            Key={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id)}
        ).get("Item")
        if not existing:
            return not_found("Receipt not found")

        update_expr_parts = []
        attr_names = {}
        attr_values = {}
        for i, (db_field, value) in enumerate(updates.items()):
            placeholder_name = f"#f{i}"
            placeholder_value = f":v{i}"
            update_expr_parts.append(f"{placeholder_name} = {placeholder_value}")
            attr_names[placeholder_name] = db_field
            attr_values[placeholder_value] = value

        table.update_item(
            Key={"PK": receipt_pk(user_id), "SK": receipt_sk(receipt_id)},
            UpdateExpression="SET " + ", ".join(update_expr_parts),
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
        )

        return ok({"receiptId": receipt_id, "updated": list(updates.values())})
    except Exception as exc:  # noqa: BLE001 - top-level Lambda guard
        print(f"Error updating receipt {receipt_id} for user {user_id}: {exc}")
        return server_error("Could not update receipt")

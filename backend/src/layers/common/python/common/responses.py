import json


def _build(status_code: int, body: dict) -> dict:
    """Build an API Gateway Lambda proxy response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def ok(body: dict) -> dict:
    return _build(200, body)


def created(body: dict) -> dict:
    return _build(201, body)


def bad_request(message: str) -> dict:
    return _build(400, {"error": message})


def unauthorized(message: str = "Unauthorized") -> dict:
    return _build(401, {"error": message})


def not_found(message: str = "Not found") -> dict:
    return _build(404, {"error": message})


def server_error(message: str = "Internal server error") -> dict:
    return _build(500, {"error": message})

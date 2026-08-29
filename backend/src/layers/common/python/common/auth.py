def get_user_id(event: dict) -> str | None:
    """Extract the Cognito user's sub (unique user id) from the API Gateway
    authorizer claims that Cognito injects into the request context once
    the Cognito Authorizer has verified the request's JWT."""
    try:
        return event["requestContext"]["authorizer"]["claims"]["sub"]
    except (KeyError, TypeError):
        return None

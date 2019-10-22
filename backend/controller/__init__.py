from flask import request, current_app
from flask_restplus import abort
from functools import wraps

from backend.service import JWTService
from backend.errors.access_error import AccessError
from .error_handler import ErrorHandler


def auth_required():
    jwt_verifier = JWTService()

    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if current_app.config.get("LOGIN_DISABLED"):
                return func(*args, **kwargs)
            elif request.headers.get("Authorization"):
                try:
                    auth_header = request.headers.get("Authorization")
                    jwt_verifier.verify_header(auth_header)
                    return func(*args, **kwargs)
                except AccessError as e:
                    abort(401, error=str(e))
            else:
                abort(401, error="Unauthorized")
        return decorated_view
    return decorator

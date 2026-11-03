
from functools import wraps
from flask import request, jsonify, make_response
from werkzeug.security import check_password_hash
import jwt

from extensions import users, token_blocklist
from config import SECRET_KEY


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization", "")

        if request.authorization and request.authorization.type.lower() == "basic":
            auth = request.authorization

            current_user = users.find_one({
                "user_id": auth.username
            })

            if current_user is None or not check_password_hash(
                current_user.get("password_hash", ""),
                auth.password or ""
            ):
                return make_response(
                    jsonify({"error": "Invalid username or password"}),
                    401
                )

            return f(current_user, *args, **kwargs)

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return make_response(
                jsonify({"error": "Authentication is required"}),
                401
            )

        try:
            data = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            jti = data.get("jti")

            if not jti:
                return make_response(
                    jsonify({"error": "Invalid token"}),
                    401
                )

            if token_blocklist.find_one({"jti": jti}):
                return make_response(
                    jsonify({"error": "Token has been revoked"}),
                    401
                )

            current_user = users.find_one({
                "user_id": data["user_id"]
            })

            if current_user is None:
                return make_response(
                    jsonify({"error": "User not found"}),
                    401
                )

        except jwt.ExpiredSignatureError:
            return make_response(
                jsonify({"error": "Token has expired"}),
                401
            )

        except jwt.InvalidTokenError:
            return make_response(
                jsonify({"error": "Invalid token"}),
                401
            )

        return f(current_user, *args, **kwargs)

    return decorated


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.get("role") not in allowed_roles:
                return make_response(
                    jsonify({
                        "error": "You do not have permission "
                                 "to perform this action"
                    }),
                    403
                )

            return f(current_user, *args, **kwargs)

        return decorated

    return decorator

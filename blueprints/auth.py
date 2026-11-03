
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from datetime import datetime, timedelta, timezone
import jwt
import uuid

from extensions import users, token_blocklist
from config import SECRET_KEY
from decorators import token_required

auth_bp = Blueprint("auth", __name__)


# Register a new user
@auth_bp.route("/api/v1.0/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True)

    if data is None:
        data = request.form.to_dict()

    if not isinstance(data, dict):
        return make_response(
            jsonify({"error": "Please provide valid JSON data"}),
            400
        )

    user_id = data.get("user_id")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([user_id, name, email, password]):
        return make_response(
            jsonify({
                "error": "user_id, name, email and password are required"
            }),
            400
        )

    if not all(
        isinstance(value, str)
        for value in [user_id, name, email, password]
    ):
        return make_response(
            jsonify({"error": "All fields must be text"}),
            400
        )

    user_id = user_id.strip()
    name = name.strip()
    email = email.strip().lower()

    if not user_id or not name or not email or not password.strip():
        return make_response(
            jsonify({"error": "Fields cannot be empty"}),
            400
        )

    if len(password) < 8:
        return make_response(
            jsonify({"error": "Password must be at least 8 characters"}),
            400
        )

    if users.find_one({"user_id": user_id}):
        return make_response(
            jsonify({"error": "User ID already exists"}),
            409
        )

    if users.find_one({"email": email}):
        return make_response(
            jsonify({"error": "Email already exists"}),
            409
        )

    new_user = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": "staff",
        "password_hash": generate_password_hash(password)
    }

    users.insert_one(new_user)

    return make_response(
        jsonify({
            "message": "User registered successfully",
            "user_id": user_id,
            "role": "staff"
        }),
        201
    )


# User login
@auth_bp.route("/api/v1.0/login", methods=["POST"])
def login():
    auth = request.authorization
    

    if auth and auth.type.lower() == "basic":
        user_id = auth.username
        password = auth.password
    else:
        auth_data = request.get_json(silent=True)

        if not isinstance(auth_data, dict):
            return make_response(
                jsonify({"error": "Please provide valid JSON data"}),
                400
            )

        user_id = auth_data.get("user_id")
        password = auth_data.get("password")

    if not user_id or not password:
        return make_response(
            jsonify({"error": "user_id and password are required"}),
            400
        )

    user = users.find_one({"user_id": user_id})

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return make_response(
            jsonify({"error": "Invalid user ID or password"}),
            401
        )

    token = jwt.encode(
        {
            "user_id": user["user_id"],
            "role": user["role"],
            "jti": uuid.uuid4().hex,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return make_response(
        jsonify({
            "message": "Login successful",
            "token": token
        }),
        200
    )


# Logout user
@auth_bp.route("/api/v1.0/logout", methods=["POST"])
@token_required
def logout(current_user):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1]

    data = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"]
    )

    jti = data["jti"]
    expires_at = datetime.fromtimestamp(
        data["exp"],
        timezone.utc
    )

    token_blocklist.update_one(
        {"jti": jti},
        {
            "$setOnInsert": {
                "jti": jti,
                "user_id": current_user["user_id"],
                "expires_at": expires_at
            }
        },
        upsert=True
    )

    return make_response(
        jsonify({"message": "Logout successful. Token revoked."}),
        200
    )

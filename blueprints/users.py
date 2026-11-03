from flask import Blueprint, jsonify, make_response, request
from extensions import users
from helpers import convert_object_ids
from decorators import role_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/api/v1.0/users", methods=["GET"])
@role_required("admin")
def get_all_users(current_user):
    user_list = list(
        users.find(
            {},
            {"password_hash": 0}
        )
    )

    return make_response(
        jsonify(convert_object_ids(user_list)),
        200
    )


@users_bp.route(
    "/api/v1.0/users/<user_id>",
    methods=["GET"]
)
@role_required("admin")
def get_one_user(current_user, user_id):
    user = users.find_one(
        {"user_id": user_id},
        {"password_hash": 0}
    )

    if user is None:
        return make_response(
            jsonify({"error": "User not found"}),
            404
        )

    return make_response(
        jsonify(convert_object_ids(user)),
        200
    )


@users_bp.route(
    "/api/v1.0/users/<user_id>",
    methods=["PUT"]
)
@role_required("admin")
def update_user(current_user, user_id):
    user = users.find_one({"user_id": user_id})

    if user is None:
        return make_response(
            jsonify({"error": "User not found"}),
            404
        )

    data = request.get_json(silent=True)

    if data is None:
        data = request.form.to_dict()

    if not isinstance(data, dict) or not data:
        return make_response(
            jsonify({"error": "Request body is required"}),
            400
        )

    allowed_fields = ["name", "email"]
    update_data = {
        key: data[key]
        for key in allowed_fields
        if key in data
    }

    if not update_data:
        return make_response(
            jsonify({"error": "No valid fields to update"}),
            400
        )

    for field, value in update_data.items():
        if not isinstance(value, str) or not value.strip():
            return make_response(
                jsonify({"error": f"Invalid {field}"}),
                400
            )

    if "email" in update_data:
        existing_user = users.find_one({
            "email": update_data["email"],
            "user_id": {"$ne": user_id}
        })

        if existing_user:
            return make_response(
                jsonify({"error": "Email already exists"}),
                409
            )

    users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )

    updated_user = users.find_one(
        {"user_id": user_id},
        {"password_hash": 0}
    )

    return make_response(
        jsonify(convert_object_ids(updated_user)),
        200
    )


@users_bp.route(
    "/api/v1.0/users/<user_id>",
    methods=["DELETE"]
)
@role_required("admin")
def delete_user(current_user, user_id):
    if user_id == current_user.get("user_id"):
        return make_response(
            jsonify({"error": "You cannot delete your own account"}),
            403
        )

    result = users.delete_one({"user_id": user_id})

    if result.deleted_count == 0:
        return make_response(
            jsonify({"error": "User not found"}),
            404
        )

    return make_response(
        jsonify({"message": "User deleted successfully"}),
        200
    )

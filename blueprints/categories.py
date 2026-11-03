
from flask import Blueprint, jsonify, make_response, request
from extensions import categories
from helpers import convert_object_ids
from decorators import role_required

categories_bp = Blueprint("categories", __name__)


@categories_bp.before_request
def check_permission():
    if request.method in ["POST", "PUT", "DELETE"]:
        @role_required("admin")
        def check(current_user):
            return None
        return check()


# GET all categories and POST a new category
@categories_bp.route("/api/v1.0/categories", methods=["GET", "POST"])
def get_all_categories():

    # GET: return all categories
    if request.method == "GET":
        category_list = list(categories.find())

        return make_response(
            jsonify(convert_object_ids(category_list)),
            200
        )

    # create a new category
    if request.method == "POST":
        data = request.get_json(silent=True)

        if data is None:
            data = request.form.to_dict()

        if not data:
            return make_response(
                jsonify({"error": "Request body is required"}),
                400
            )

        if not data.get("category_id") or not data.get("name"):
            return make_response(
                jsonify({"error": "category_id and name are required"}),
                400
            )

        existing_category = categories.find_one(
            {"category_id": data["category_id"]}
        )

        if existing_category:
            return make_response(
                jsonify({"error": "Category already exists"}),
                409
            )

        categories.insert_one(data)

        return make_response(
            jsonify({"message": "Category created successfully"}),
            201
        )


# GET, PUT, and DELETE one category
@categories_bp.route(
    "/api/v1.0/categories/<category_id>",
    methods=["GET", "PUT", "DELETE"]
)
def get_one_category(category_id):

    # GET: return one category
    if request.method == "GET":
        category = categories.find_one(
            {"category_id": category_id}
        )

        if category is None:
            return make_response(
                jsonify({"error": "Category not found"}),
                404
            )

        return make_response(
            jsonify(convert_object_ids(category)),
            200
        )

    # PUT: update an existing category
    if request.method == "PUT":
        data = request.get_json(silent=True)

        if data is None:
            data = request.form.to_dict()

        if not data:
            return make_response(
                jsonify({"error": "Request body is required"}),
                400
            )

        update_fields = {
            key: data[key]
            for key in ["name", "slug", "description", "subcategories"]
            if key in data
        }

        if not update_fields:
            return make_response(
                jsonify({"error": "No fields to update"}),
                400
            )

        result = categories.update_one(
            {"category_id": category_id},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            return make_response(
                jsonify({"error": "Category not found"}),
                404
            )

        return make_response(
            jsonify({"message": "Category updated successfully"}),
            200
        )

    # DELETE: delete an existing category
    if request.method == "DELETE":
        result = categories.delete_one(
            {"category_id": category_id}
        )

        if result.deleted_count == 0:
            return make_response(
                jsonify({"error": "Category not found"}),
                404
            )

        return make_response(
            jsonify({"message": "Category deleted successfully"}),
            200
        )

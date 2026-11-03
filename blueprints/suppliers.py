from flask import Blueprint, jsonify, make_response, request
from extensions import suppliers
from helpers import convert_object_ids
from decorators import role_required

suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.before_request
def check_permission():
    if request.method in ["POST", "PUT", "DELETE"]:
        @role_required("admin")
        def check(current_user):
            return None
        return check()


# GET all suppliers and POST a new supplier
@suppliers_bp.route("/api/v1.0/suppliers", methods=["GET", "POST"])
def get_all_suppliers():

    # GET: return all suppliers
    if request.method == "GET":
        supplier_list = list(suppliers.find())

        return make_response(
            jsonify(convert_object_ids(supplier_list)),
            200
        )

    # POST: create a new supplier
    if request.method == "POST":
        data = request.get_json(silent=True)

        if data is None:
            data = request.form.to_dict()

        if not data:
            return make_response(
                jsonify({"error": "Request body is required"}),
                400
            )

        if not data.get("supplier_id") or not data.get("name"):
            return make_response(
                jsonify({"error": "supplier_id and name are required"}),
                400
            )

        existing_supplier = suppliers.find_one(
            {"supplier_id": data["supplier_id"]}
        )

        if existing_supplier:
            return make_response(
                jsonify({"error": "Supplier already exists"}),
                409
            )

        suppliers.insert_one(data)

        return make_response(
            jsonify({"message": "Supplier created successfully"}),
            201
        )


# GET one supplier
@suppliers_bp.route(
    "/api/v1.0/suppliers/<supplier_id>",
    methods=["GET"]
)
def get_one_supplier(supplier_id):
    supplier = suppliers.find_one(
        {"supplier_id": supplier_id},
        {"_id": 0}
    )

    if supplier is None:
        return make_response(
            jsonify({"error": "Supplier not found"}),
            404
        )

    return make_response(
        jsonify(convert_object_ids(supplier)),
        200
    )


# UPDATE one supplier
@suppliers_bp.route(
    "/api/v1.0/suppliers/<supplier_id>",
    methods=["PUT"]
)
def update_supplier(supplier_id):
    data = request.get_json(silent=True)

    if data is None:
        data = request.form.to_dict()

    if not data:
        return make_response(
            jsonify({"error": "No data provided"}),
            400
        )

    allowed_fields = [
        "name", "email", "phone", "address", "contacts",
        "payment_terms_days", "default_lead_time_days", "rating", "status"
    ]
    update_fields = {field: data[field] for field in allowed_fields if field in data}
    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    result = suppliers.update_one(
        {"supplier_id": supplier_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return make_response(
            jsonify({"error": "Supplier not found"}),
            404
        )

    return make_response(
        jsonify({"message": "Supplier updated successfully"}),
        200
    )


# DELETE one supplier
@suppliers_bp.route(
    "/api/v1.0/suppliers/<supplier_id>",
    methods=["DELETE"]
)
def delete_supplier(supplier_id):
    result = suppliers.delete_one(
        {"supplier_id": supplier_id}
    )

    if result.deleted_count == 0:
        return make_response(
            jsonify({"error": "Supplier not found"}),
            404
        )

    return make_response(
        jsonify({"message": "Supplier deleted successfully"}),
        200
    )
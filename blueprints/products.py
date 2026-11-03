
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timezone
from bson import ObjectId

from extensions import products
from decorators import token_required, role_required
from helpers import convert_object_ids

products_bp = Blueprint("products", __name__)

def get_product_form_data():
    data = request.get_json(silent=True)
    if data is not None:
        return data

    data = request.form.to_dict()
    if not data:
        return data

    if "price" in data:
        try:
            data["price"] = float(data["price"])
        except (ValueError, TypeError):
            return {**data, "price": None}

    if "category" in data:
        data["category"] = {"name": data["category"]}

    if "supplier" in data:
        data["supplier"] = {"name": data["supplier"]}

    if "stock" in data:
        try:
            quantity = int(data["stock"])
            min_level = int(data.pop("min_level", "0"))
        except (ValueError, TypeError):
            quantity = None
            min_level = None
        warehouse = data.pop("warehouse", "WH-MAIN")
        data["stock"] = {
            "quantity": quantity,
            "min_level": min_level,
            "locations": [{"warehouse": warehouse, "quantity": quantity}]
        }

    return data



# Show all products with pagination
@products_bp.route("/api/v1.0/products", methods=["GET"])
@token_required
def show_all_products(current_user):
    try:
        page_num = int(request.args.get("pn", 1))
        page_size = int(request.args.get("ps", 10))

        if page_num < 1 or page_size < 1 or page_size > 100:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "pn must be >= 1 and ps must be between 1 and 100"}), 400

    page_start = page_size * (page_num - 1)
    data = [
        convert_object_ids(product)
        for product in products.find().skip(page_start).limit(page_size)
    ]
    return jsonify(data), 200


# Fetch one product
@products_bp.route("/api/v1.0/products/<product_id>", methods=["GET"])
def show_one_product(product_id):
    product = products.find_one({"product_id": product_id})
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(convert_object_ids(product)), 200


# Add a new product
@products_bp.route("/api/v1.0/products", methods=["POST"])
@role_required("admin")
def add_product(current_user):
    new_product = get_product_form_data()

    if not isinstance(new_product, dict):
        return jsonify({"error": "Please provide valid JSON data"}), 400

    required_fields = [
        "product_id", "sku", "name", "category",
        "supplier", "price", "stock"
    ]

    for field in required_fields:
        if field not in new_product:
            return jsonify({"error": f"Missing field: {field}"}), 400

    price = new_product["price"]
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        return jsonify({"error": "price must be a non-negative number"}), 400

    stock = new_product["stock"]
    if not isinstance(stock, dict):
        return jsonify({"error": "stock must be a JSON object"}), 400

    for field in ["quantity", "min_level"]:
        value = stock.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return jsonify({"error": f"stock.{field} must be a non-negative integer"}), 400

    if products.find_one({
        "$or": [
            {"product_id": new_product["product_id"]},
            {"sku": new_product["sku"]}
        ]
    }):
        return jsonify({"error": "product_id or sku already exists"}), 409

    result = products.insert_one(new_product)
    new_product["_id"] = str(result.inserted_id)
    return jsonify(convert_object_ids(new_product)), 201


# Edit an existing product
@products_bp.route("/api/v1.0/products/<product_id>", methods=["PUT"])
@role_required("admin")
def edit_product(current_user, product_id):
    updated_data = get_product_form_data()

    if not isinstance(updated_data, dict) or not updated_data:
        return jsonify({"error": "Please provide valid JSON data"}), 400

    allowed_fields = [
        "sku", "name", "description", "status",
        "category", "supplier", "price",
        "tags", "specifications"
    ]

    data_to_update = {
        field: updated_data[field]
        for field in allowed_fields
        if field in updated_data
    }

    if not data_to_update:
        return jsonify({"error": "No valid fields provided to update"}), 400

    if "price" in data_to_update:
        price = data_to_update["price"]
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            return jsonify({"error": "price must be a non-negative number"}), 400

    if "stock" in data_to_update:
        stock = data_to_update["stock"]
        if not isinstance(stock, dict):
            return jsonify({"error": "stock must be a JSON object"}), 400

        for field in ["quantity", "min_level"]:
            if field in stock:
                value = stock[field]
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    return jsonify({"error": f"stock.{field} must be a non-negative integer"}), 400

    result = products.update_one(
        {"product_id": product_id},
        {"$set": data_to_update}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Product not found"}), 404

    updated_product = products.find_one({"product_id": product_id})
    return jsonify(convert_object_ids(updated_product)), 200


# Delete a product (admin only)
@products_bp.route("/api/v1.0/products/<product_id>", methods=["DELETE"])
@role_required("admin")
def delete_product(current_user, product_id):
    result = products.delete_one({"product_id": product_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product deleted successfully!"}), 200


# Update stock and record movement
@products_bp.route("/api/v1.0/products/<product_id>/stock", methods=["PUT"])
@role_required("admin", "staff")
def update_product_stock(current_user, product_id):
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
        if "quantity" in data:
            try:
                data["quantity"] = int(data["quantity"])
            except (ValueError, TypeError):
                pass

    if not isinstance(data, dict):
        return jsonify({"error": "Please provide valid JSON data"}), 400

    movement_type = data.get("type")
    quantity = data.get("quantity")
    note = data.get("reason", data.get("note", ""))
    warehouse = data.get("warehouse")

    if movement_type == "in":
        movement_type = "received"
    elif movement_type == "out":
        movement_type = "sold"

    if movement_type not in ["received", "sold", "adjusted"]:
        return jsonify({"error": "Invalid movement type"}), 400

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    if not isinstance(warehouse, str) or not warehouse.strip():
        return jsonify({"error": "Warehouse is required"}), 400

    product = products.find_one({"product_id": product_id})
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    current_stock = product.get("stock", {})
    current_quantity = current_stock.get("quantity", 0)
    locations = current_stock.get("locations", [])
    location = next(
        (item for item in locations if item.get("warehouse") == warehouse),
        None
    )

    if location is None:
        return jsonify({"error": "Warehouse not found"}), 404

    location_quantity = location.get("quantity", 0)
    change = -quantity if movement_type == "sold" else quantity

    if location_quantity + change < 0:
        return jsonify({"error": "Not enough stock in this warehouse"}), 400

    new_quantity = current_quantity + change
    movement = {
        "_id": ObjectId(),
        "type": movement_type,
        "quantity": quantity,
        "reason": note,
        "warehouse": warehouse,
        "date": datetime.now(timezone.utc),
        "recorded_by": {
            "_id": current_user["_id"],
            "name": current_user.get("name", "")
        }
    }

    if movement_type == "sold":
        movement["unit_price"] = product.get("price", 0)

    result = products.update_one(
        {
            "product_id": product_id,
            "stock.quantity": current_quantity,
            "stock.locations": {
                "$elemMatch": {
                    "warehouse": warehouse,
                    "quantity": location_quantity
                }
            }
        },
        {
            "$inc": {
                "stock.quantity": change,
                "stock.locations.$.quantity": change
            },
            "$push": {"stock_movements": movement}
        }
    )

    if result.modified_count == 0:
        return jsonify({
            "error": "Stock changed or could not be updated. Please try again."
        }), 409

    return jsonify({
        "message": "Stock updated successfully",
        "product_id": product_id,
        "previous_quantity": current_quantity,
        "new_quantity": new_quantity,
        "movement": convert_object_ids(movement)
    }), 200



# Get low-stock products
@products_bp.route("/api/v1.0/products/low-stock", methods=["GET"])
@role_required("admin", "staff")
def get_low_stock_products(current_user):
    low_stock_products = products.find({
        "$expr": {
            "$lte": ["$stock.quantity", "$stock.min_level"]
        }
    })

    data = []
    for product in low_stock_products:
        data.append({
            "product_id": product.get("product_id"),
            "sku": product.get("sku"),
            "name": product.get("name"),
            "stock": product.get("stock", {})
        })

    return jsonify({
        "count": len(data),
        "products": convert_object_ids(data)
    }), 200


# Get stock movement history
@products_bp.route(
    "/api/v1.0/products/<product_id>/stock-movements",
    methods=["GET"])
@role_required("admin", "staff")
def get_stock_movements(current_user, product_id):
    product = products.find_one(
        {"product_id": product_id},
        {"stock_movements": 1, "product_id": 1, "_id": 0}
    )

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    movements = product.get("stock_movements", [])
    movement_type = request.args.get("type")

    if movement_type:
        if movement_type == "in":
            movement_type = "received"
        elif movement_type == "out":
            movement_type = "sold"
        if movement_type not in ["received", "sold", "adjusted"]:
            return jsonify({"error": "Invalid movement type"}), 400
        movements = [
            movement for movement in movements
            if movement.get("type") == movement_type
        ]

    try:
        page_num = int(request.args.get("pn", 1))
        page_size = int(request.args.get("ps", 10))
        if page_num < 1 or page_size < 1 or page_size > 100:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "error": "pn must be >= 1 and ps must be between 1 and 100"
        }), 400

    total = len(movements)
    page_start = page_size * (page_num - 1)

    return jsonify({
        "product_id": product_id,
        "count": total,
        "page": page_num,
        "page_size": page_size,
        "stock_movements": convert_object_ids(
            movements[page_start:page_start + page_size]
        )
    }), 200


# Search products
@products_bp.route("/api/v1.0/products/search", methods=["GET"])
def search_products():
    query = {}

    name = request.args.get("name")
    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    category = request.args.get("category")
    if category:
        query["category.name"] = {"$regex": category, "$options": "i"}

    status = request.args.get("status")
    if status:
        query["status"] = status

    data = [
        convert_object_ids(product)
        for product in products.find(query).limit(100)
    ]

    return jsonify({
        "total": len(data),
        "products": data
    }), 200

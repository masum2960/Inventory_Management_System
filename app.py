
from itertools import product

from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient
from bson import ObjectId
from datetime import date

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["inventory_management"]

products = db["products"]
categories = db["categories"]
suppliers = db["suppliers"]
users = db["users"]

# Convert MongoDB ObjectIds into strings
def convert_object_ids(data):
    if isinstance(data, dict):
        return {
            key: convert_object_ids(value)
            for key, value in data.items()
        }

    elif isinstance(data, list):
        return [convert_object_ids(item) for item in data]

    elif isinstance(data, ObjectId):
        return str(data)

    else:
        return data

# This is a welcome route
@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Welcome to Inventory Management API</h1>", 200)


# Show all products with pagination
@app.route("/api/v1.0/products", methods=["GET"])
def show_all_products():
    page_num, page_size = 1, 10

    if request.args.get("pn"):
        page_num = int(request.args.get("pn"))

    if request.args.get("ps"):
        page_size = int(request.args.get("ps"))

    page_start = page_size * (page_num - 1)

    data_to_return = []

    for product in products.find().skip(page_start).limit(page_size):
        product = convert_object_ids(product)
        data_to_return.append(product)

    return make_response(jsonify(data_to_return), 200)


# Fetch one product by product_id
@app.route("/api/v1.0/products/<product_id>", methods=["GET"])
def show_one_product(product_id):
    product = products.find_one({"product_id": product_id})

    if product is None:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )
    product = convert_object_ids(product)
    return make_response(jsonify(product), 200)





# Add a new product
@app.route("/api/v1.0/products", methods=["POST"])
def add_product():
    new_product = request.get_json(silent=True)

    if not isinstance(new_product, dict):
        return make_response(
            jsonify({"error": "Please provide valid JSON data"}),
            400
        )

    required_fields = [
        "product_id", "sku", "name", "category",
        "supplier", "price", "stock"
    ]

    for field in required_fields:
        if field not in new_product:
            return make_response(
                jsonify({"error": f"Missing field: {field}"}),
                400
            )

    price = new_product["price"]
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        return make_response(
            jsonify({"error": "price must be a non-negative number"}),
            400
        )

    stock = new_product["stock"]
    if not isinstance(stock, dict):
        return make_response(
            jsonify({"error": "stock must be a JSON object"}),
            400
        )

    for field in ["quantity", "min_level"]:
        value = stock.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return make_response(
                jsonify({"error": f"stock.{field} must be a non-negative integer"}),
                400
            )

    if products.find_one({
        "$or": [
            {"product_id": new_product["product_id"]},
            {"sku": new_product["sku"]}
        ]
    }):
        return make_response(
            jsonify({"error": "product_id or sku already exists"}),
            409
        )

    result = products.insert_one(new_product)
    new_product["_id"] = str(result.inserted_id)

    return make_response(
        jsonify(convert_object_ids(new_product)),
        201
    )





# Edit an existing product
@app.route("/api/v1.0/products/<product_id>", methods=["PUT"])
def edit_product(product_id):
    updated_data = request.get_json(silent=True)

    # Check that valid JSON was provided
    if not isinstance(updated_data, dict) or not updated_data:
        return make_response(
            jsonify({"error": "Please provide valid JSON data"}),
            400
        )

    # Fields that can be updated
    allowed_fields = [
        "sku", "name", "description", "status",
        "category", "supplier", "price", "stock",
        "locations", "stock_movements",
        "price_history", "tags", "specifications"
    ]

    # Keep only allowed fields
    data_to_update = {
        field: updated_data[field]
        for field in allowed_fields
        if field in updated_data
    }

    if not data_to_update:
        return make_response(
            jsonify({"error": "No valid fields provided to update"}),
            400
        )

    # Validate price if supplied
    if "price" in data_to_update:
        price = data_to_update["price"]

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
        ):
            return make_response(
                jsonify({"error": "price must be a non-negative number"}),
                400
            )

    # Validate stock if supplied
    if "stock" in data_to_update:
        stock = data_to_update["stock"]

        if not isinstance(stock, dict):
            return make_response(
                jsonify({"error": "stock must be a JSON object"}),
                400
            )

        for field in ["quantity", "min_level"]:
            if field in stock:
                value = stock[field]

                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                ):
                    return make_response(
                        jsonify({
                            "error": f"stock.{field} must be a non-negative integer"
                        }),
                        400
                    )

    # Find and update the product
    result = products.update_one(
        {"product_id": product_id},
        {"$set": data_to_update}
    )

    if result.matched_count == 0:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )

    # Retrieve the updated product
    updated_product = products.find_one(
        {"product_id": product_id}
    )

    updated_product = convert_object_ids(updated_product)

    return make_response(jsonify(updated_product), 200)




# Delete a product
@app.route("/api/v1.0/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    result = products.delete_one({
        "product_id": product_id
    })

    if result.deleted_count == 0:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )

    return make_response(
        jsonify({"message": "Product deleted successfully!"}),
        200
    )






# Search and filter products
@app.route("/api/v1.0/products/search", methods=["GET"])
def search_products():
    query = {}

    # Search by product name
    name = request.args.get("name")
    if name:
        query["name"] = {
            "$regex": name,
            "$options": "i"
        }

    # Filter by category name
    category = request.args.get("category")
    if category:
        query["category.name"] = {
            "$regex": category,
            "$options": "i"
        }

    # Filter by product status
    status = request.args.get("status")
    if status:
        query["status"] = status

    # Retrieve matching products
    data_to_return = []

    for product in products.find(query).limit(100):
        data_to_return.append(convert_object_ids(product))

    return make_response(
        jsonify({
            "total": len(data_to_return),
            "products": data_to_return
        }),
        200
    )










if __name__ == "__main__":
    app.run(debug=True, port=5001)

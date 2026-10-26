
from itertools import product

from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient
from bson import ObjectId

import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

app.config['SECRET_KEY'] = 'itsmemasum'

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



# Require a valid JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Read the token from the Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]

            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

        # Check whether the token exists
        if not token:
            return make_response(
                jsonify({"error": "Token is missing"}),
                401
            )

        try:
            # Decode and verify the token
            data = jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=["HS256"]
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





# User login
@app.route("/api/v1.0/login", methods=["POST"])
def login():
    from werkzeug.security import check_password_hash

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
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return make_response(
        jsonify({
            "message": "Login successful",
            "token": token
        }),
        200
    )



# This is a welcome route
@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Welcome to Inventory Management API</h1>", 200)


# Show all products with pagination
@app.route('/api/v1.0/products', methods=["GET"])
@token_required
def show_all_products(current_user):
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
@token_required
def add_product(current_user):
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
@token_required
def edit_product(current_user, product_id):
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
@token_required
def delete_product(current_user, product_id):
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





# Get all categories
@app.route("/api/v1.0/categories", methods=["GET"])
def get_all_categories():
    data_to_return = []

    for category in categories.find():
        data_to_return.append(convert_object_ids(category))

    return make_response(jsonify(data_to_return), 200)


# Get one category
@app.route("/api/v1.0/categories/<category_id>", methods=["GET"])
def get_one_category(category_id):
    category = categories.find_one({
        "category_id": category_id
    })

    if category is None:
        return make_response(
            jsonify({"error": "Category not found"}),
            404
        )

    return make_response(
        jsonify(convert_object_ids(category)),
        200
    )



# Get one supplier
@app.route("/api/v1.0/suppliers/<supplier_id>", methods=["GET"])
def get_one_supplier(supplier_id):
    supplier = suppliers.find_one({
        "supplier_id": supplier_id
    })

    if supplier is None:
        return make_response(
            jsonify({"error": "Supplier not found"}),
            404
        )

    return make_response(
        jsonify(convert_object_ids(supplier)),
        200
    )


# Get all suppliers
@app.route("/api/v1.0/suppliers", methods=["GET"])
def get_all_suppliers():
    data_to_return = []

    for supplier in suppliers.find():
        data_to_return.append(convert_object_ids(supplier))

    return make_response(jsonify(data_to_return), 200)




# Get all users
@app.route("/api/v1.0/users", methods=["GET"])
@token_required
def get_all_users(current_user):
    data_to_return = []

    for user in users.find():
        data_to_return.append({
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "role": user.get("role")
        })

    return make_response(jsonify(data_to_return), 200)



# Get one user

@app.route("/api/v1.0/users/<user_id>", methods=["GET"])
@token_required
def get_one_user(current_user, user_id):
    user = users.find_one({
        "user_id": user_id
    })

    if user is None:
        return make_response(
            jsonify({"error": "User not found"}),
            404
        )

    return make_response(
        jsonify(convert_object_ids(user)),
        200
    )










if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5001)
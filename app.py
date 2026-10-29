
from itertools import product

from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient
from bson import ObjectId

import jwt
import uuid
from functools import wraps
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'itsmemasum'

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["inventory_management"]

products = db["products"]
categories = db["categories"]
suppliers = db["suppliers"]
users = db["users"]
token_blocklist = db["token_blocklist"]
token_blocklist.create_index(
    "expires_at",
    expireAfterSeconds=0
)

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

            # Check that the token has a unique ID
            jti = data.get("jti")

            if not jti:
                return make_response(
                    jsonify({"error": "Invalid token"}),
                    401
                )

            # Reject tokens that have been revoked
            if token_blocklist.find_one({"jti": jti}):
                return make_response(
                    jsonify({"error": "Token has been revoked"}),
                    401
                )

            # Find the current user in MongoDB
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




# Restrict access by user role
def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.get("role") not in allowed_roles:
                return make_response(jsonify({
                    "error": "You do not have permission to perform this action"
                }), 403)

            return f(current_user, *args, **kwargs)

        return decorated
    return decorator



# Register a new user
@app.route("/api/v1.0/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True)

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
            "jti": uuid.uuid4().hex,
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
    




# Logout user
@app.route("/api/v1.0/logout", methods=["POST"])
@token_required
def logout(current_user):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1]

    data = jwt.decode(
        token,
        app.config["SECRET_KEY"],
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
@role_required("admin")
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



# Update product stock and record the movement
@app.route("/api/v1.0/products/<product_id>/stock", methods=["PUT"])
@role_required("admin", "staff")
def update_product_stock(current_user, product_id):
    from datetime import datetime, timezone

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response(jsonify({
            "error": "Please provide valid JSON data"
        }), 400)

    movement_type = data.get("type")
    quantity = data.get("quantity")
    note = data.get("note", "")

    if movement_type not in ["in", "out"]:
        return make_response(jsonify({
            "error": "Type must be 'in' or 'out'"
        }), 400)

    if type(quantity) is not int or quantity <= 0:
        return make_response(jsonify({
            "error": "Quantity must be a positive integer"
        }), 400)

    product = products.find_one({"product_id": product_id})

    if product is None:
        return make_response(jsonify({
            "error": "Product not found"
        }), 404)

    current_stock = product.get("stock", {})
    current_quantity = current_stock.get("quantity", 0)

    if movement_type == "out" and quantity > current_quantity:
        return make_response(jsonify({
            "error": "Not enough stock available"
        }), 400)

    change = quantity if movement_type == "in" else -quantity
    new_quantity = current_quantity + change

    movement = {
        "type": movement_type,
        "quantity": quantity,
        "note": note,
        "date": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user.get("user_id")
    }

    result = products.update_one(
        {
            "product_id": product_id,
            "stock.quantity": current_quantity
        },
        {
            "$inc": {"stock.quantity": change},
            "$push": {"stock_movements": movement}
        }
    )

    if result.modified_count == 0:
        return make_response(jsonify({
            "error": "Stock changed or could not be updated. Please try again."
        }), 409)

    return make_response(jsonify({
        "message": "Stock updated successfully",
        "product_id": product_id,
        "previous_quantity": current_quantity,
        "new_quantity": new_quantity,
        "movement": movement
    }), 200)



# Get products with low stock
@app.route("/api/v1.0/products/low-stock", methods=["GET"])
@token_required
def get_low_stock_products(current_user):
    low_stock_products = products.find({
        "$expr": {
            "$lte": [
                "$stock.quantity",
                "$stock.min_level"
            ]
        }
    })

    data_to_return = []

    for product in low_stock_products:
        data_to_return.append({
            "product_id": product.get("product_id"),
            "sku": product.get("sku"),
            "name": product.get("name"),
            "stock": product.get("stock", {})
        })

    return make_response(jsonify({
        "count": len(data_to_return),
        "products": convert_object_ids(data_to_return)
    }), 200)



# Get stock movement history for one product
@app.route(
    "/api/v1.0/products/<product_id>/stock-movements",
    methods=["GET"]
)
@token_required
def get_stock_movements(current_user, product_id):
    product = products.find_one(
        {"product_id": product_id},
        {"stock_movements": 1, "product_id": 1, "_id": 0}
    )

    if product is None:
        return make_response(jsonify({
            "error": "Product not found"
        }), 404)

    movements = product.get("stock_movements", [])

    movement_type = request.args.get("type")

    if movement_type:
        if movement_type not in ["in", "out"]:
            return make_response(jsonify({
                "error": "Type must be 'in' or 'out'"
            }), 400)

        movements = [
            movement for movement in movements
            if movement.get("type") == movement_type
        ]

    total = len(movements)

    try:
        page_num = int(request.args.get("pn", 1))
        page_size = int(request.args.get("ps", 10))

        if page_num < 1 or page_size < 1 or page_size > 100:
            raise ValueError

    except (ValueError, TypeError):
        return make_response(jsonify({
            "error": "pn must be >= 1 and ps must be between 1 and 100"
        }), 400)

    page_start = page_size * (page_num - 1)
    paginated_movements = movements[page_start:page_start + page_size]

    return make_response(jsonify({
        "product_id": product_id,
        "count": total,
        "page": page_num,
        "page_size": page_size,
        "stock_movements": convert_object_ids(paginated_movements)
    }), 200)




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


# Restrict access by user role
def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            print("DEBUG ROLE:", current_user.get("role"), "| ALLOWED:", allowed_roles)
            if current_user.get("role") not in allowed_roles:
                return make_response(jsonify({
                    "error": "You do not have permission to perform this action"
                }), 403)

            return f(current_user, *args, **kwargs)

        return decorated
    return decorator

# Get all users
@app.route("/api/v1.0/users", methods=["GET"])
@role_required("admin")
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
@role_required("admin")
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
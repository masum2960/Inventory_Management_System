
from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient

from datetime import date

app = Flask(__name__)

# Mongo connection
client = MongoClient("mongodb://localhost:27017")
db = client.inventory_management
products = db.products

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
        product["_id"] = str(product["_id"])
        data_to_return.append(product)

    return make_response(jsonify(data_to_return), 200)


# Fetch one product by Product_ID
@app.route("/api/v1.0/products/<product_id>", methods=["GET"])
def show_one_product(product_id):
    product = products.find_one({"Product_ID": product_id})

    if product is None:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )

    product["_id"] = str(product["_id"])

    return make_response(jsonify(product), 200)



# Add a new product
@app.route("/api/v1.0/products", methods=["POST"])
def add_product():
    new_product = request.get_json(silent=True)

    # Check that the request contains JSON
    if not isinstance(new_product, dict):
        return make_response(
            jsonify({"error": "Please provide valid JSON data"}),
            400
        )

    # Required product fields
    required_fields = [
        "Product_ID", "SKU", "Product_Name", "Category",
        "Supplier", "Price_GBP", "Quantity", "Reorder_Level",
        "Warehouse_Zone", "Restock_Date", "Availability",
        "Description"
    ]

    # Check for missing or empty fields
    for field in required_fields:
        if field not in new_product:
            return make_response(
                jsonify({"error": f"Missing field: {field}"}),
                400
            )

        if (
            new_product[field] is None
            or (
                isinstance(new_product[field], str)
                and not new_product[field].strip()
            )
        ):
            return make_response(
                jsonify({"error": f"{field} cannot be empty"}),
                400
            )

    # Check numeric values
    price = new_product["Price_GBP"]
    quantity = new_product["Quantity"]
    reorder_level = new_product["Reorder_Level"]

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or price < 0
    ):
        return make_response(
            jsonify({"error": "Price_GBP must be a non-negative number"}),
            400
        )

    for field, value in [
        ("Quantity", quantity),
        ("Reorder_Level", reorder_level)
    ]:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            return make_response(
                jsonify({"error": f"{field} must be a non-negative integer"}),
                400
            )



    # Validate the restock date
    try:
        date.fromisoformat(new_product["Restock_Date"])
    except (ValueError, TypeError):
        return make_response(
            jsonify({
                "error": "Restock_Date must be a valid date in YYYY-MM-DD format"
            }),
            400
        )

    # Validate availability
    allowed_availability = [
        "In Stock",
        "Low Stock",
        "Out of Stock"
    ]

    if new_product["Availability"] not in allowed_availability:
        return make_response(
            jsonify({
                "error": "Availability must be In Stock, Low Stock, or Out of Stock"
            }),
            400
        )












    # Check for duplicate product ID or SKU
    if products.find_one({
        "$or": [
            {"Product_ID": new_product["Product_ID"]},
            {"SKU": new_product["SKU"]}
        ]
    }):
        return make_response(
            jsonify({"error": "Product_ID or SKU already exists"}),
            409
        )

    # Insert the valid product
    result = products.insert_one(new_product)
    new_product["_id"] = str(result.inserted_id)

    return make_response(jsonify(new_product), 201)




# Edit an existing product
@app.route("/api/v1.0/products/<product_id>", methods=["PUT"])
def edit_product(product_id):
    updated_data = request.get_json()

    if not updated_data or not isinstance(updated_data, dict):
        return make_response(
            jsonify({"error": "Please provide valid JSON data"}),
            400
        )

    allowed_fields = [
        "SKU", "Product_Name", "Category", "Supplier",
        "Price_GBP", "Quantity", "Reorder_Level",
        "Warehouse_Zone", "Restock_Date",
        "Availability", "Description"
    ]

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

    result = products.update_one(
        {"Product_ID": product_id},
        {"$set": data_to_update}
    )

    if result.matched_count == 0:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )

    updated_product = products.find_one({"Product_ID": product_id})
    updated_product["_id"] = str(updated_product["_id"])

    return make_response(jsonify(updated_product), 200)




# Delete a product
@app.route("/api/v1.0/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    result = products.delete_one({"Product_ID": product_id})

    if result.deleted_count == 0:
        return make_response(
            jsonify({"error": "Product not found"}),
            404
        )

    return make_response(
        jsonify({"Message": "Product deleted successfully!"}),
        200
    )




# Search and filter products
@app.route("/api/v1.0/products/search", methods=["GET"])
def search_products():
    query = {}

    # Search by product name
    name = request.args.get("name")
    if name:
        query["Product_Name"] = {
            "$regex": name,
            "$options": "i"
        }

    # Filter by category
    category = request.args.get("category")
    if category:
        query["Category"] = category

    # Filter by availability
    availability = request.args.get("availability")
    if availability:
        query["Availability"] = availability

    data_to_return = []

    for product in products.find(query).limit(100):
        product["_id"] = str(product["_id"])
        data_to_return.append(product)

    return make_response(
        jsonify({
            "total": len(data_to_return),
            "products": data_to_return
        }),
        200
    )










if __name__ == "__main__":
    app.run(debug=True, port=5001)

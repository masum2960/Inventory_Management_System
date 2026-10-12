
import json
from pathlib import Path
from pymongo import MongoClient, ReplaceOne

# Connect to your local MongoDB
client = MongoClient("mongodb://localhost:27017")

try:
    # Check that MongoDB is running
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")

    # Select a separate database and collection
    db = client["inventory_management"]
    products = db["products"]

    # Find and read the JSON dataset in this folder
    file_path = Path(__file__).parent / "inventory_manag_dataset.json"

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # Check the dataset format
    if not isinstance(data, list) or len(data) != 100:
        raise ValueError("Expected a JSON list containing 100 products.")

    # Import products using Product_ID to avoid duplicate records
    operations = [
        ReplaceOne(
            {"Product_ID": product["Product_ID"]},
            product,
            upsert=True
        )
        for product in data
    ]

    result = products.bulk_write(operations)

    # Verify the number of products in the collection
    total = products.count_documents({})

    print(f"Products inserted: {result.upserted_count}")
    print(f"Products updated: {result.modified_count}")
    print(f"Total products in database: {total}")

finally:
    client.close()

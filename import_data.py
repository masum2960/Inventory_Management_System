from pathlib import Path
from pymongo import MongoClient, ReplaceOne
from bson import json_util

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017")

try:
    # Check MongoDB connection
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")

    db = client["inventory_management"]
    collections = {
        "products": "product_id",
        "categories": "category_id",
        "suppliers": "supplier_id",
        "users": "user_id"
    }

    for collection_name, id_field in collections.items():
        collection = db[collection_name]
        file_path = (
            Path(__file__).parent
            / "inventory_datasets"
            / f"{collection_name}.json"
        )

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        # Read the JSON dataset
        with file_path.open("r", encoding="utf-8") as file:
            data = json_util.load(file)

        if not isinstance(data, list) or not data:
            raise ValueError(f"Invalid {collection_name} dataset")

        record_ids = []
        for record in data:
            if not isinstance(record, dict) or not record.get(id_field):
                raise ValueError(f"Missing {id_field} in {collection_name}")
            record_ids.append(record[id_field])

        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"Duplicate {id_field} in {collection_name}")

        existing_ids = set(collection.distinct(id_field))
        if existing_ids - set(record_ids):
            raise RuntimeError(
                f"{collection_name} contains records from another dataset. "
                "Back up your database and use clean collections."
            )

        operations = [
            ReplaceOne({id_field: record[id_field]}, record, upsert=True)
            for record in data
        ]
        result = collection.bulk_write(operations)
        total = collection.count_documents({})

        print(f"\n{collection_name} import completed!")
        print(f"Inserted: {result.upserted_count}")
        print(f"Updated: {result.modified_count}")
        print(f"Total: {total}")

finally:
    client.close()

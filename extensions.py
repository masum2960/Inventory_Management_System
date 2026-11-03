from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["inventory_management"]

# Define collections
products = db["products"]
categories = db["categories"]
suppliers = db["suppliers"]
users = db["users"]
token_blocklist = db["token_blocklist"]

# Remove expired revoked tokens automatically
token_blocklist.create_index(
    "expires_at",
    expireAfterSeconds=0
)
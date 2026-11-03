from bson import ObjectId


def convert_object_ids(data):
    """Convert MongoDB ObjectIds to strings for JSON responses."""
    if isinstance(data, dict):
        return {
            key: convert_object_ids(value)
            for key, value in data.items()
        }

    elif isinstance(data, list):
        return [
            convert_object_ids(item)
            for item in data
        ]

    elif isinstance(data, ObjectId):
        return str(data)

    return data
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["drift"]

def get_camera_economics(camera_code: str) -> dict:
    cam = db.cameras.find_one({"camera_id": camera_code})

    if not cam:
        raise ValueError(f"Camera not found: {camera_code}")

    aisles = cam["aisles"]

    premium_indices = []
    sale_indices = []

    premium_value = 0
    sale_value = 0

    for aisle in aisles:
        idx = aisle["aisle_index"]
        aisle_type = aisle["aisle_type"]

        aisle_price = sum(p["price"] for p in aisle["products"])

        if aisle_type == "premium":
            premium_indices.append(idx)
            premium_value += aisle_price
        else:
            sale_indices.append(idx)
            sale_value += aisle_price

    total_value = premium_value + sale_value

    return {
        "total_aisles": len(aisles),
        "premium_indices": premium_indices,
        "sale_indices": sale_indices,
        "premium_value": premium_value,
        "sale_value": sale_value,
        "total_value": total_value
    }

from pymongo import MongoClient

# Mongo connection
client = MongoClient("mongodb://localhost:27017")
db = client.drift


def get_camera_economics(camera_code: str) -> dict:
    """
    Given a camera_code, compute economic weights
    for premium vs cheap/sale aisles.
    """

    # 1. Find the camera
    camera = db.cameras.find_one({"camera_code": camera_code})
    if not camera:
        return {"premium_weight": 0, "cheap_weight": 0}

    aisle_ids = camera.get("viewing_aisles", [])

    # 2. Fetch aisles
    aisles = list(db.aisles.find({"_id": {"$in": aisle_ids}}))

    premium_value = 0
    cheap_value = 0

    for aisle in aisles:
        value = aisle.get("total_value", 0)

        if aisle.get("aisle_type") == "premium":
            premium_value += value
        else:  # cheap/sale or standard treated as non-premium
            cheap_value += value

    total = premium_value + cheap_value
    if total == 0:
        return {"premium_weight": 0, "cheap_weight": 0}

    return {
        "premium_weight": premium_value / total,
        "cheap_weight": cheap_value / total
    }

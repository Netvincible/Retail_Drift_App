from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client.drift


def get_camera_economics(camera_code: str):
    """
    Returns ONLY economic context for a camera.
    Used by Gemini for drift calculation.

    Output keys (MUST exist):
    - total_value
    - premium_value
    """

    camera = db.cameras.find_one({"camera_code": camera_code})

    if not camera:
        raise RuntimeError(f"Camera not found: {camera_code}")

    aisle_ids = camera.get("viewing_aisles", [])

    if not aisle_ids:
        # No aisles → no economics
        return {
            "total_value": 1,
            "premium_value": 0
        }

    aisles = list(db.aisles.find({"_id": {"$in": aisle_ids}}))

    total_value = 0
    premium_value = 0

    for aisle in aisles:
        aisle_value = aisle.get("total_value", 0)
        total_value += aisle_value

        if aisle.get("aisle_type") == "premium":
            premium_value += aisle_value

    # 🔒 Prevent divide-by-zero in Gemini math
    if total_value <= 0:
        total_value = 1

    return {
        "total_value": total_value,
        "premium_value": premium_value
    }

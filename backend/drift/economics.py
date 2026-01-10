from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["drift"]
cameras = db["cameras"]


def get_camera_economics(camera_code: str):
    camera = cameras.find_one({"camera_id": camera_code})

    if not camera:
        raise ValueError(f"Camera {camera_code} not found")

    premium_indices = []
    sale_indices = []

    premium_price = 0
    sale_price = 0

    for aisle in camera["aisles"]:
        idx = aisle["aisle_index"]
        aisle_type = aisle["aisle_type"]

        aisle_total = sum(p["price"] for p in aisle["products"])

        if aisle_type == "premium":
            premium_indices.append(idx)
            premium_price += aisle_total
        else:
            sale_indices.append(idx)
            sale_price += aisle_total

    return {
        "camera_id": camera_code,
        "aisle_count": len(camera["aisles"]),
        "premium_aisle_indices": premium_indices,
        "sale_aisle_indices": sale_indices,
        "premium_total_price": premium_price,
        "sale_total_price": sale_price,
        "total_price": premium_price + sale_price
    }

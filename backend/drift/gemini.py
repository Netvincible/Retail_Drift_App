from google import genai
from google.genai import types
import cv2

client = genai.Client(api_key="Your API Key")

def get_drift_score(frame, economics: dict) -> int:
    """
    Gemini counts people in premium vs sale aisles
    and computes drift:
    ((people_premium / total_people) - (premium_value / total_value)) * 100
    """



    # Encode frame as JPEG bytes
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Failed to encode frame")

    image_part = types.Part.from_bytes(
        data=buffer.tobytes(),
        mime_type="image/jpeg"
    )

    prompt = f"""
You are analyzing a single retail CCTV frame.

Aisle layout:
- Total aisles: {economics["total_aisles"]}
- Premium aisles (0-based index, right to left): {economics["premium_indices"]}
- Sale aisles (0-based index, right to left): {economics["sale_indices"]}

Economic values:
- Premium value: {economics["premium_value"]}
- Total value: {economics["total_value"]}

DEFINITIONS:
- A person is inside an aisle if their body centroid lies within that aisle.

TASK:
1. Count people in premium aisles.
2. Count total people visible.

COMPUTATION:
If total_people == 0:
- Return 0.

Compute drift using EXACTLY:

abs((people_in_premium / total_people) - (premium_value / total_value)) * 100

RULES:
- Round to nearest integer.
- Return ONLY the integer drift value.
- No explanation.
"""


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image_part]
    )

    # Extract integer safely
    try:
        drift = int("".join(c for c in response.text if c.isdigit()))
    except Exception:
        drift = 0

    return max(drift, 0)

from google import genai
from google.genai import types
import cv2

client = genai.Client(api_key="AIzaSyCvyyFonAXXqG08X-HnCWfL0UQ4Pac89tE")

def get_drift_score(frame, economics: dict) -> int:
    """
    Gemini counts people in premium vs sale aisles
    and computes drift:
    ((people_premium / total_people) - (premium_value / total_value)) * 100
    """
    BnW_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Encode frame as JPEG bytes
    success, buffer = cv2.imencode(".jpg", BnW_frame)
    if not success:
        raise RuntimeError("Failed to encode frame")

    image_part = types.Part.from_bytes(
        data=buffer.tobytes(),
        mime_type="image/jpeg"
    )

    prompt = f"""
You are analyzing a retail CCTV frame.

Aisle layout:
- Total aisles: {economics["total_aisles"]}
- Premium aisles (0-based index, left to right): {economics["premium_indices"]}
- Sale aisles (0-based index, left to right): {economics["sale_indices"]}

Economic values:
- Premium value: {economics["premium_value"]}
- Total value: {economics["total_value"]}

TASK:
1. Count how many people are standing in premium aisles.
2. Count total people visible.
3. Compute drift using this EXACT formula:

((people_in_premium / total_people) - (premium_value / total_value)) * 100

Rules:
- If result is negative, return 0.
- Return ONLY the final integer drift value.
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

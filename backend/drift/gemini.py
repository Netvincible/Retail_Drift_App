import time
import base64
import cv2
from google import genai
from threading import Lock

# -----------------------------------
# GEMINI CLIENT (NEW SDK ONLY)
# -----------------------------------
client = genai.Client(api_key="AIzaSyBDEkadKuaqc607GIOHcLLakRBMjBg43jk")

MODEL_NAME = "gemini-2.0-flash"

# -----------------------------------
# HARD RATE LIMITING (MANDATORY)
# -----------------------------------
_LAST_CALL_TS = 0
_COOLDOWN_SECONDS = 45   # FREE TIER SAFE
_LOCK = Lock()

# -----------------------------------
# MAIN FUNCTION
# -----------------------------------
def get_drift_score(frame, economics: dict) -> int:
    """
    Calls Gemini ONCE per cooldown window.
    Returns an integer drift score between 0–100.
    """

    global _LAST_CALL_TS

    with _LOCK:
        now = time.time()
        if now - _LAST_CALL_TS < _COOLDOWN_SECONDS:
            # Do NOT call Gemini again
            return economics.get("last_score", 0)

        _LAST_CALL_TS = now

    # -----------------------------------
    # ENCODE IMAGE (JPEG → BASE64)
    # -----------------------------------
    success, jpeg = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Frame JPEG encoding failed")

    image_b64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

    # -----------------------------------
    # PROMPT (STRICT + NUMERIC)
    # -----------------------------------
    prompt = f"""
You are a retail analytics AI.

You MUST calculate a Drift Score between 0 and 100.

Definitions:
- Premium aisle value: {economics['premium_value']}
- Standard aisle value: {economics['standard_value']}
- Discount aisle value: {economics['discount_value']}
- People in premium aisle: {economics['people_premium']}
- People in standard aisle: {economics['people_standard']}
- People in discount aisle: {economics['people_discount']}

Rules:
- High crowd in discount with high premium value = HIGH drift
- High crowd in premium with premium value = LOW drift
- Ignore aesthetics, focus on revenue mismatch

Return ONLY a single integer between 0 and 100.
NO text.
NO explanation.
"""

    # -----------------------------------
    # GEMINI CALL (CORRECT FORMAT)
    # -----------------------------------
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image_b64
                }
            ]
        )

        raw = response.text.strip()

        # -----------------------------------
        # PARSE OUTPUT SAFELY
        # -----------------------------------
        score = int("".join(c for c in raw if c.isdigit()))
        score = max(0, min(100, score))

        economics["last_score"] = score
        return score

    except Exception as e:
        # NEVER CRASH WORKER
        print(f"[GEMINI ERROR] {e}")
        return economics.get("last_score", 0)

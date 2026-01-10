import base64
import json
import cv2
import os
import google.generativeai as genai

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def get_drift_score(frame, economics: dict) -> int:
    """
    Send one frame + economic context to Gemini
    and receive a drift score between 0 and 100.
    """

    # 1. Encode frame as JPEG
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        return 0

    image_base64 = base64.b64encode(buffer).decode("utf-8")

    # 2. Strict prompt (JSON-only)
    prompt = f"""
You are a retail CCTV drift analyzer.

Context:
- Premium economic weight: {economics['premium_weight']}
- Cheap/sale economic weight: {economics['cheap_weight']}

Task:
Analyze the image and estimate customer attention imbalance.
If customers are concentrated in low economic areas
while premium zones appear ignored, drift is high.

Rules:
- Output ONLY valid JSON
- No explanations
- Drift score must be between 0 and 100

Return format:
{{ "drift_score": number }}
"""

    # 3. Call Gemini
    response = model.generate_content(
        [
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": image_base64
            }
        ],
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 50
        }
    )

    # 4. Parse safely
    try:
        result = json.loads(response.text)
        score = int(result.get("drift_score", 0))
        return max(0, min(score, 100))
    except Exception:
        return 0

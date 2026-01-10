# drift/worker.py
import time
from drift.gemini import get_drift_score
from drift.economics import get_camera_economics
from drift.state import DRIFT_STATE, LATEST_FRAME, AI_ENABLED


def drift_worker(camera_code: str):
    """
    Background worker for ONE camera.
    Runs only when AI_ENABLED[camera_code] is True.
    """

    print(f"[WORKER READY] {camera_code}")

    while True:
        time.sleep(6)  # Gemini interval (hard limit)

        # AI globally disabled or camera disabled
        if not AI_ENABLED.get(camera_code, False):
            continue

        try:
            if camera_code not in LATEST_FRAME:
                continue

            frame = LATEST_FRAME[camera_code]
            economics = get_camera_economics(camera_code)

            drift_score = get_drift_score(frame, economics)

            DRIFT_STATE[camera_code]["score"] = drift_score
            DRIFT_STATE[camera_code]["last_updated"] = time.time()

            print(f"[DRIFT] {camera_code}: {drift_score}")

        except Exception as e:
            print(f"[DRIFT WORKER ERROR] {camera_code}: {e}")
            time.sleep(10)  # cooldown on API / quota errors

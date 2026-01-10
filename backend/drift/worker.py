import time
from drift.gemini import get_drift_score
from drift.economics import get_camera_economics
from drift.state import LATEST_FRAME, DRIFT_STATE


def drift_worker(camera_code: str):
    """
    Background worker that updates drift score
    every 6 seconds for a given camera.
    """

    while True:
        time.sleep(6) #gemini interval
        print(f"[WORKER STARTED] {camera_code}")
        try:
            # 1. Ensure a frame exists
            if camera_code not in LATEST_FRAME:
                time.sleep(1)
                continue

            frame = LATEST_FRAME[camera_code]

            # 2. Get economic context
            economics = get_camera_economics(camera_code)

            # 3. Call Gemini (slow, isolated)
            drift_score = get_drift_score(frame, economics)

            # 4. Update shared drift state
            DRIFT_STATE[camera_code]["score"] = drift_score
            DRIFT_STATE[camera_code]["last_updated"] = time.time()

        except Exception as e:
            # Never crash the worker
            print(f"[DRIFT WORKER ERROR] {camera_code}: {e}")


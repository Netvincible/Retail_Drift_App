import time
import threading
import cv2

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from drift.overlay import draw_drift_border
from drift.worker import drift_worker
from drift.state import LATEST_FRAME, DRIFT_STATE

# -----------------------------
# APP SETUP
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# CAMERA CONFIGURATION
# -----------------------------
CAMERA_CONFIG = {
    "CAM-01": "cameras/cam_01.mp4",
    # Add more cameras here later
}

# -----------------------------
# VIDEO STREAM GENERATOR
# -----------------------------
def camera_stream(camera_code: str):
    cap = cv2.VideoCapture(CAMERA_CONFIG[camera_code])

    while True:
        ret, frame = cap.read()

        # Loop video
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Save latest frame for background worker
        LATEST_FRAME[camera_code] = frame.copy()

        # Read latest drift score
        drift_score = DRIFT_STATE[camera_code]["score"]

        # Draw overlay
        frame = draw_drift_border(frame, drift_score)

        # Encode as JPEG
        _, buffer = cv2.imencode(".jpg", frame)

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

        # ~30 FPS
        time.sleep(0.03)

# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.get("/video/{camera_code}")
def video_feed(camera_code: str):
    return StreamingResponse(
        camera_stream(camera_code),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/drift/{camera_code}")
def get_drift(camera_code: str):
    state = DRIFT_STATE.get(camera_code, {})
    return {
        "camera": camera_code,
        "drift_score": state.get("score", 0),
        "last_updated": state.get("last_updated", 0)
    }

# -----------------------------
# STARTUP: WORKERS
# -----------------------------
@app.on_event("startup")
def start_background_workers():
    for cam in CAMERA_CONFIG:
        DRIFT_STATE[cam] = {"score": 0, "last_updated": 0}
        threading.Thread(
            target=drift_worker,
            args=(cam,),
            daemon=True
        ).start()

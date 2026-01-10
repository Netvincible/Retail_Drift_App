import time
import threading
import cv2
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import drift.state as state
from drift.worker import drift_worker
from drift.overlay import draw_drift_border
from drift.control import RUNNING

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
    # add more cameras later
}

# -----------------------------
# AI CONTROL ENDPOINTS
# -----------------------------
@app.post("/ai/start/{camera_code}")
def ai_start(camera_code: str):
    state.AI_ENABLED[camera_code] = True
    return {"status": "AI started", "camera": camera_code}


@app.post("/ai/stop/{camera_code}")
def ai_stop(camera_code: str):
    state.AI_ENABLED[camera_code] = False
    return {"status": "AI stopped", "camera": camera_code}

@app.post("/camera/start/{camera_code}")
def start_camera(camera_code: str):
    RUNNING[camera_code] = True
    return {"status": f"{camera_code} started"}

@app.post("/camera/stop/{camera_code}")
def stop_camera(camera_code: str):
    RUNNING[camera_code] = False
    return {"status": f"{camera_code} stopped"}

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

        # Save frame for AI worker
        state.LATEST_FRAME[camera_code] = frame.copy()

        # Read drift score
        drift_score = state.DRIFT_STATE[camera_code]["score"]

        # Overlay
        frame = draw_drift_border(frame, drift_score)

        # Encode JPEG
        _, buffer = cv2.imencode(".jpg", frame)

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

        time.sleep(0.03)  # ~30 FPS

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
    state_data = state.DRIFT_STATE.get(camera_code, {})
    return {
        "camera": camera_code,
        "drift_score": state_data.get("score", 0),
        "last_updated": state_data.get("last_updated", 0)
    }

# -----------------------------
# STARTUP: WORKERS (SAFE)
# -----------------------------
WORKERS_STARTED = False

@app.on_event("startup")
def startup_workers():
    global WORKERS_STARTED
    if WORKERS_STARTED:
        return

    WORKERS_STARTED = True

    for cam in CAMERA_CONFIG:
        state.DRIFT_STATE[cam] = {"score": 0, "last_updated": 0}
        state.AI_ENABLED[cam] = False   # ✅ IMPORTANT
        RUNNING[cam] = True             # camera stream always on

        threading.Thread(
            target=drift_worker,
            args=(cam,),
            daemon=True
        ).start()

    print("[SYSTEM] Workers initialized (idle)")


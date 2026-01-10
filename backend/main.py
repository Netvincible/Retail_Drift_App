from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import time

app = FastAPI()

# Allow React to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. LOAD THE VIDEO
# Ensure video.mp4 is in the same folder as this file
video_path = "video.mp4"
def generate_frames():
    cap = cv2.VideoCapture(video_path)

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # --- THE FIX: SLOW DOWN THE STREAM ---
        # 0.03 seconds sleep = roughly 30 Frames Per Second
        time.sleep(0.03)
        # -------------------------------------

        # Draw the Red Box (The "Dead Zone")
        # Ensure these coordinates are valid for your video resolution!
        # If your video is small, these numbers might be off-screen.
        height, width, _ = frame.shape
        cv2.rectangle(frame, (width//2, height//2), (width-100, height-100), (0, 0, 255), 4)

        # Add Text
        cv2.putText(frame, "DRIFT DETECTED", (width//2, height//2 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        # Encode the frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/")
def read_root():
    return {"status": "Vision Engine Online"}

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

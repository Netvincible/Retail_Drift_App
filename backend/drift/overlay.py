import cv2


def draw_drift_border(frame, drift_score: int):
    """
    Draw a red border around the frame.
    Border brightness and thickness scale with drift_score (0–100).
    """

    if frame is None:
        return frame

    # Clamp drift score
    drift_score = max(0, min(drift_score, 100))

    height, width, _ = frame.shape

    # Red intensity scales with drift
    red_intensity = int((drift_score / 100) * 255)

    # Border thickness scales with drift
    thickness = 2 + int(drift_score / 15)

    color = (0, 0, red_intensity)  # BGR (Red channel)

    # Draw rectangle border
    cv2.rectangle(
        frame,
        (0, 0),
        (width - 1, height - 1),
        color,
        thickness
    )

    # Optional drift text
    cv2.putText(
        frame,
        f"DRIFT: {drift_score}%",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        3
    )

    return frame

import cv2


def open_video(source):
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video source: {source}")
    return capture


def draw_detections(frame, result):
    colors = {
        "Happy": (0, 200, 0),
        "Normal": (0, 220, 220),
        "Sad": (0, 0, 220),
        "Surprised": (220, 0, 220),
    }
    for face in result.get("faces", []):
        x1, y1, x2, y2 = face["box"]
        emotion = face["emotion"]
        confidence = face["confidence"]
        color = colors.get(emotion, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{emotion} {confidence:.0%}",
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
    return frame

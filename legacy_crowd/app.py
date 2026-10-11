import sys
from pathlib import Path

import cv2
import streamlit as st

# Đảm bảo import được từ cả root và legacy_crowd
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_inference import EMOTION_CLASSES as EMOTIONS, predict_emotion_from_frame
from video_stream import draw_detections, open_video

DEFAULT_VIDEO = ROOT / "Resources" / "Video" / "2021-09-22 17.32.08.mp4"

st.set_page_config(page_title="Crowd Emotion Monitor", page_icon="📹", layout="wide")
st.title("Crowd Emotion Monitor")
st.caption("Week 2 monitoring dashboard | Real-time AI inference")

with st.sidebar:
    st.header("Video source")
    source_type = st.radio("Source", ["Test video", "Webcam"], index=0)
    frame_delay = st.slider("Playback delay (seconds)", 0.01, 0.20, 0.05)
    start = st.button("Start monitoring", type="primary", width="stretch")
    stop = st.button("Stop", width="stretch")

if "running" not in st.session_state:
    st.session_state.running = False
if "capture" not in st.session_state:
    st.session_state.capture = None
if "history" not in st.session_state:
    st.session_state.history = []

if start:
    if st.session_state.capture is not None:
        st.session_state.capture.release()
    source = 0 if source_type == "Webcam" else str(DEFAULT_VIDEO)
    try:
        st.session_state.capture = open_video(source)
        st.session_state.history = []
        st.session_state.running = True
        st.rerun()
    except RuntimeError as error:
        st.session_state.capture = None
        st.session_state.running = False
        st.error(str(error))

if stop:
    st.session_state.running = False
    if st.session_state.capture is not None:
        st.session_state.capture.release()
        st.session_state.capture = None
    st.rerun()


@st.fragment(run_every=frame_delay if st.session_state.running else None)
def render_monitor():
    capture = st.session_state.capture
    if not st.session_state.running or capture is None:
        st.info("Nhấn 'Start monitoring' ở thanh bên để bắt đầu giám sát luồng video.")
        return

    success, frame = capture.read()
    if not success and source_type == "Test video":
        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        success, frame = capture.read()

    if not success:
        st.session_state.running = False
        if capture is not None:
            capture.release()
        st.session_state.capture = None
        st.warning("Video stream ended or could not read a frame.")
        return

    result = predict_emotion_from_frame(frame)
    annotated = draw_detections(frame, result)
    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

    insights = result.get("crowd_insights", {})
    distribution = insights.get("distribution", {em: 0.0 for em in EMOTIONS})
    alert_level = insights.get("alert_level", "NORMAL")
    alert_message = insights.get("alert_message", "Dòng người lưu thông ổn định")
    total_faces = insights.get("total_faces", len(result.get("faces", [])))
    risk = distribution.get("Sad", 0.0) + distribution.get("Surprised", 0.0)

    status_color = {"NORMAL": "🟢", "WARNING": "🟠", "CRITICAL": "🔴"}.get(alert_level, "🟢")

    left, right = st.columns([2.1, 1])
    with left:
        st.subheader("Live camera feed")
        st.image(annotated, channels="RGB", width="stretch")

    with right:
        st.subheader("Security status")
        st.metric("Alert level", f"{status_color} {alert_level}", f"Risk {risk:.0%}")
        st.metric("Detected faces", total_faces)
        top_emotion = max(distribution, key=distribution.get) if distribution else "Normal"
        st.metric("Dominant emotion", top_emotion)
        st.subheader("Emotion distribution")
        st.bar_chart(distribution)

    st.subheader("Emotion trend")
    st.session_state.history.append(distribution)
    st.session_state.history = st.session_state.history[-40:]
    trend_data = {
        emotion: [item.get(emotion, 0.0) for item in st.session_state.history]
        for emotion in EMOTIONS
    }
    st.line_chart(trend_data)
    st.caption(f"{alert_message} | AI-01 2-Tier Pipeline")


render_monitor()

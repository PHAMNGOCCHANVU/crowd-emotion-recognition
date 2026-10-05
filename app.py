from pathlib import Path

import cv2
import streamlit as st

from ai_inference import EMOTION_CLASSES as EMOTIONS, predict_emotion_from_frame
from video_stream import draw_detections, open_video

ROOT = Path(__file__).parent
DEFAULT_VIDEO = ROOT / "Resources" / "Video" / "2021-09-22 17.32.08.mp4"

st.set_page_config(page_title="Crowd Emotion Monitor", page_icon="📹", layout="wide")
st.title("Crowd Emotion Monitor")
st.caption("Week 1 dashboard prototype | Mock AI inference")

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
    except RuntimeError as error:
        st.session_state.capture = None
        st.session_state.running = False
        st.error(str(error))
if stop:
    st.session_state.running = False
    if st.session_state.capture is not None:
        st.session_state.capture.release()
        st.session_state.capture = None

left, right = st.columns([2.1, 1])
with left:
    st.subheader("Live camera feed")
    video_placeholder = st.empty()
with right:
    st.subheader("Security status")
    status_placeholder = st.empty()
    metric_face = st.empty()
    metric_emotion = st.empty()
    st.subheader("Emotion distribution")
    chart_placeholder = st.empty()

st.subheader("Emotion trend")
trend_placeholder = st.empty()

@st.fragment(run_every=frame_delay if st.session_state.running else None)
def render_monitor():
    capture = st.session_state.capture
    if not st.session_state.running or capture is None:
        video_placeholder.info("Press Start monitoring to begin.")
        return

    success, frame = capture.read()
    if not success and source_type == "Test video":
        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        success, frame = capture.read()
    if not success:
        st.session_state.running = False
        capture.release()
        st.session_state.capture = None
        video_placeholder.warning("Video stream ended or could not read a frame.")
        return

    result = predict_emotion_from_frame(frame)
    annotated = draw_detections(frame, result)
    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    video_placeholder.image(annotated, channels="RGB", width="stretch")

    insights = result["crowd_insights"]
    distribution = insights["distribution"]
    alert_level = insights["alert_level"]
    alert_message = insights["alert_message"]
    risk = distribution["Sad"] + distribution["Surprised"]
    status_color = {"NORMAL": "🟢", "WARNING": "🟠", "CRITICAL": "🔴"}[alert_level]
    status_placeholder.metric("Alert level", f"{status_color} {alert_level}", f"Risk {risk:.0%}")
    metric_face.metric("Detected faces", insights["total_faces"])
    top_emotion = max(distribution, key=distribution.get)
    metric_emotion.metric("Dominant emotion", top_emotion)
    chart_placeholder.bar_chart(distribution)

    st.session_state.history.append(distribution)
    st.session_state.history = st.session_state.history[-40:]
    trend_data = {
        emotion: [item[emotion] for item in st.session_state.history]
        for emotion in EMOTIONS
    }
    trend_placeholder.line_chart(trend_data)
    st.caption(f"{alert_message} | AI-01")


render_monitor()

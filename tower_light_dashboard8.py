import streamlit as st
import cv2
import numpy as np
import time
import pandas as pd
from datetime import datetime
from collections import deque

st.set_page_config(page_title="Industrial Command Center", layout="wide")
st.title("🏭 Smart Factory: Operator Command Center")

# --- 1. INITIALIZATION ---
if "logs" not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=["Timestamp", "Event", "Status"])

# --- 2. LAYOUT ---
col_metrics = st.columns(3)
status_metric = col_metrics[0].empty()
uptime_metric = col_metrics[1].empty()
alert_metric = col_metrics[2].empty()

col_view, col_log = st.columns([1, 1])
video_placeholder = col_view.empty()
log_placeholder = col_log.empty()

# --- 3. PROCESSING ---
def add_log(event, status):
    new_entry = {"Timestamp": datetime.now().strftime("%H:%M:%S"), "Event": event, "Status": status}
    st.session_state.logs = pd.concat([pd.DataFrame([new_entry]), st.session_state.logs]).head(10)

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    status_buffer = deque(maxlen=10)
    last_status = "IDLE"
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Logic
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        red_mask = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
        green_mask = cv2.inRange(hsv, np.array([40, 100, 70]), np.array([80, 255, 255]))
        
        val = 0
        if cv2.countNonZero(red_mask) > 500: val = -1
        elif cv2.countNonZero(green_mask) > 500: val = 1
            
        status_buffer.append(val)
        
        # Debouncing/Smoothing Logic
        current = "IDLE"
        if status_buffer.count(1) > 7: current = "OPERATIONAL"
        elif status_buffer.count(-1) > 7: current = "CRITICAL"
        
        # Trigger Notification if state changes
        if current != last_status:
            if current == "CRITICAL":
                add_log("ALERT: Machine Malfunction", "DISPATCHED TO OPERATOR")
            elif current == "OPERATIONAL":
                add_log("SUCCESS: Machine Normal", "SYSTEM CLEAR")
            last_status = current
            
        # UI Updates
        video_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
        status_metric.metric("Machine State", current)
        uptime_metric.metric("Active Alerts", "1" if current == "CRITICAL" else "0")
        alert_metric.metric("Operator", "Online")
        
        # Show Log as an Impressive Table
        log_placeholder.subheader("Live Dispatch Log")
        log_placeholder.table(st.session_state.logs)
        
        time.sleep(0.04)
    cap.release()

if st.button("Initialize Production Monitor"):
    process_video('towerlight.mp4')

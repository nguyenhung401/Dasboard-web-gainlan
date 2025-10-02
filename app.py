import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="📊 Exam Proctor Dashboard – Silent Mode", layout="wide")
st.title("📊 Exam Proctor Dashboard – Silent Mode")

if "dnd_until" not in st.session_state:
    st.session_state.dnd_until = 0.0

st.sidebar.header("Cài đặt")
if st.sidebar.button("🔕 Bật DND 2 phút"):
    st.session_state.dnd_until = time.time() + 120

if time.time() < st.session_state.dnd_until:
    remain = int(st.session_state.dnd_until - time.time())
    st.warning(f"🔕 DND đang bật ({remain}s còn lại)")
else:
    st.info("✅ Silent Mode đang hoạt động")

# Dữ liệu mẫu
sample_events = [
    {"ts":"2025-10-02 10:01:05","student":"HS01","event":"pose_right","severity":"YELLOW"},
    {"ts":"2025-10-02 10:01:06","student":"HS01","event":"audio_ask","severity":"RED"},
    {"ts":"2025-10-02 10:03:20","student":"HS02","event":"pose_down","severity":"YELLOW"},
]
df = pd.DataFrame(sample_events)

st.subheader("📌 Sự kiện mới nhất")
def style_rows(row):
    color = {'RED':'#ffcccc','YELLOW':'#fff2cc','GREEN':'#ccffcc'}.get(row['severity'],'#f6f6f6')
    return [f'background-color: {color}']*len(row)

st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True, height=300)

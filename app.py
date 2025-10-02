import streamlit as st
import pandas as pd
import time, hashlib

st.set_page_config(page_title="📊 Exam Proctor Dashboard – Silent Mode (RBAC)", layout="wide")

# ========== AUTH + RBAC ==========
def sha256(s:str)->str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# TIP: Đưa danh sách người dùng vào secrets khi deploy (không commit lên GitHub)
# Ví dụ secrets.toml:
# [auth]
# USERS = [
#   { user = "admin1", pass_sha256 = "<SHA256>", role = "admin" },
#   { user = "gv01",   pass_sha256 = "<SHA256>", role = "proctor", exam_scope = "E01" },
#   { user = "view1",  pass_sha256 = "<SHA256>", role = "viewer" }
# ]
DEMO_USERS = [
    {"user":"admin1", "pass_sha256": sha256("admin123"),   "role":"admin"},
    {"user":"gv01",   "pass_sha256": sha256("proctor123"), "role":"proctor", "exam_scope":"E01"},
    {"user":"view1",  "pass_sha256": sha256("viewer123"),  "role":"viewer"}
]
USERS = st.secrets.get("auth", {}).get("USERS", DEMO_USERS)
USERMAP = {u["user"]: u for u in USERS if "user" in u and "pass_sha256" in u}

# Session state
defaults = {
    "auth_ok": False, "auth_user": None, "auth_role": None, "auth_exam_scope": None,
    "auth_attempts": 0, "auth_locked_until": 0.0,
    "dnd_until": 0.0
}
for k,v in defaults.items():
    st.session_state.setdefault(k, v)

def login_form():
    st.sidebar.subheader("🔐 Đăng nhập")
    if time.time() < st.session_state.auth_locked_until:
        remain = int(st.session_state.auth_locked_until - time.time())
        st.sidebar.error(f"Tạm khóa đăng nhập ({remain}s) do nhập sai nhiều lần.")
        return

    with st.sidebar.form("login"):
        u = st.text_input("Tài khoản", placeholder="vd: gv01")
        p = st.text_input("Mật khẩu", type="password", placeholder="••••••")
        ok = st.form_submit_button("Đăng nhập")
    if ok:
        rec = USERMAP.get(u)
        if rec and sha256(p) == rec["pass_sha256"]:
            st.session_state.auth_ok = True
            st.session_state.auth_user = u
            st.session_state.auth_role = rec.get("role","viewer")
            st.session_state.auth_exam_scope = rec.get("exam_scope")
            st.session_state.auth_attempts = 0
            st.sidebar.success(f"Chào {u} · vai trò {st.session_state.auth_role}")
        else:
            st.session_state.auth_attempts += 1
            left = max(0, 5 - st.session_state.auth_attempts)
            st.sidebar.error(f"Sai tài khoản hoặc mật khẩu. Còn {left} lần.")
            if st.session_state.auth_attempts >= 5:
                st.session_state.auth_locked_until = time.time() + 60  # khóa 60s

def logout_btn():
    if st.sidebar.button("🚪 Đăng xuất"):
        for k in ["auth_ok","auth_user","auth_role","auth_exam_scope"]:
            st.session_state[k] = None
        st.session_state.auth_ok = False

def require_roles(*roles):
    def deco(fn):
        def wrapped(*args, **kwargs):
            if not st.session_state.auth_ok:
                st.warning("Cần đăng nhập."); st.stop()
            if st.session_state.auth_role not in roles:
                st.error("Bạn không có quyền truy cập mục này."); st.stop()
            return fn(*args, **kwargs)
        return wrapped
    return deco

# Gate
if not st.session_state.auth_ok:
    login_form()
    st.stop()
else:
    st.sidebar.caption(f"Đăng nhập: **{st.session_state.auth_user}** · vai trò **{st.session_state.auth_role}**")
    if st.session_state.auth_exam_scope:
        st.sidebar.caption(f"Phạm vi kỳ thi: **{st.session_state.auth_exam_scope}**")
    logout_btn()

# ========== UI CHÍNH ==========
st.title("📊 Exam Proctor Dashboard – Silent Mode (RBAC)")

# Sidebar: chỉ ADMIN & PROCTOR mới có quyền bật DND toàn hệ thống
st.sidebar.header("Cài đặt")
if st.session_state.auth_role in ["admin","proctor"]:
    if st.sidebar.button("🔕 Bật DND 2 phút"):
        st.session_state.dnd_until = time.time() + 120
else:
    st.sidebar.caption("Viewer: chỉ xem, không có quyền bật DND.")

# Banner trạng thái
if time.time() < st.session_state.dnd_until:
    remain = int(st.session_state.dnd_until - time.time())
    st.warning(f"🔕 DND đang bật (còn {remain}s) — hệ thống chỉ ghi log, không phát cảnh báo.")
else:
    st.info("✅ Silent Mode đang hoạt động (không phát âm thanh).")

# ===== Dữ liệu mẫu (giữ nguyên nhưng có lọc theo scope) =====
sample_events = [
    {"ts":"2025-10-02 10:01:05","exam_id":"E01","student":"HS01","event":"pose_right","severity":"YELLOW"},
    {"ts":"2025-10-02 10:01:06","exam_id":"E01","student":"HS01","event":"audio_ask","severity":"RED"},
    {"ts":"2025-10-02 10:03:20","exam_id":"E02","student":"HS02","event":"pose_down","severity":"YELLOW"},
]
df = pd.DataFrame(sample_events)

# Lọc theo phạm vi kỳ thi nếu proctor bị giới hạn
scope = st.session_state.auth_exam_scope
if scope:
    df = df[df["exam_id"] == scope]

st.subheader("📌 Sự kiện mới nhất")
def style_rows(row):
    color = {'RED':'#ffcccc','YELLOW':'#fff2cc','GREEN':'#ccffcc'}.get(row['severity'],'#f6f6f6')
    return [f'background-color: {color}']*len(row)

st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True, height=320)

# Panel ADMIN: cấu hình hệ thống (chỉ admin)
@require_roles("admin")
def admin_panel():
    st.subheader("⚙️ Cấu hình hệ thống (Admin)")
    col1, col2 = st.columns(2)
    with col1:
        pitch_down = st.number_input("Ngưỡng Pitch cúi xuống (độ)", value=-15)
        yaw_side   = st.number_input("Ngưỡng Yaw quay ngang (độ)", value=20)
    with col2:
        fusion_red    = st.text_input("Rule RED", value="(audio_ask and pose_suspect) or (rf_detect and pose_suspect)")
        fusion_yellow = st.text_input("Rule YELLOW", value="pose_suspect or audio_ask or rf_detect")
    if st.button("💾 Lưu cấu hình"):
        st.success("Đã lưu (demo). Khi triển khai thực tế: gửi API tới server.")

with st.expander("Khu vực quản trị (Admin-only)"):
    if st.session_state.auth_role == "admin":
        admin_panel()
    else:
        st.info("Bạn không có quyền admin.")

# Panel PROCTOR: ACK sự kiện (admin/proctor)
if st.session_state.auth_role in ["admin","proctor"]:
    st.subheader("🛡️ Bảng điều khiển giám thị")
    if df.empty:
        st.info("Không có sự kiện thuộc phạm vi của bạn.")
    else:
        idx = st.selectbox("Chọn dòng để ACK", options=list(df.index),
                           format_func=lambda i: f"{df.loc[i,'exam_id']} · {df.loc[i,'student']} · {df.loc[i,'event']}")
        if st.button("✅ ACK sự kiện"):
            st.success(f"Đã ACK dòng #{idx} (demo). Thực tế: gọi API /ack để ghi nhận.")

# Viewer: chỉ đọc
st.subheader("👁️ Tổng quan rủi ro (Read-only)")
df_risk = pd.DataFrame([
    {"exam_id":"E01","student":"HS01","risk":7},
    {"exam_id":"E02","student":"HS02","risk":3},
])
if scope:
    df_risk = df_risk[df_risk["exam_id"] == scope]
st.dataframe(df_risk, use_container_width=True)

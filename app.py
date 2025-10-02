import streamlit as st
import pandas as pd
import time, hashlib, json, os

st.set_page_config(page_title="📊 Exam Proctor Dashboard – RBAC + User Mgmt", layout="wide")

USERS_FILE = "users.json"

def sha256(s:str)->str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

DEMO_USERS = [
    {"user":"admin1", "pass_sha256": sha256("admin123"),   "role":"admin"},
    {"user":"gv01",   "pass_sha256": sha256("proctor123"), "role":"proctor", "exam_scope":"E01"},
    {"user":"view1",  "pass_sha256": sha256("viewer123"),  "role":"viewer"}
]

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all("user" in u and "pass_sha256" in u for u in data):
                return data
        except Exception:
            pass
    sec_users = st.secrets.get("auth", {}).get("USERS", [])
    if isinstance(sec_users, list) and sec_users:
        return sec_users
    return DEMO_USERS

def save_users(users:list):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

USERS = load_users()
USERMAP = {u["user"]: u for u in USERS}

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
                st.session_state.auth_locked_until = time.time() + 60

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

if not st.session_state.auth_ok:
    login_form(); st.stop()
else:
    st.sidebar.caption(f"Đăng nhập: **{st.session_state.auth_user}** · vai trò **{st.session_state.auth_role}**")
    if st.session_state.auth_exam_scope:
        st.sidebar.caption(f"Phạm vi kỳ thi: **{st.session_state.auth_exam_scope}**")
    logout_btn()

st.title("📊 Exam Proctor Dashboard – RBAC + User Management")

st.sidebar.header("Cài đặt")
if st.session_state.auth_role in ["admin","proctor"]:
    if st.sidebar.button("🔕 Bật DND 2 phút"):
        st.session_state.dnd_until = time.time() + 120
else:
    st.sidebar.caption("Viewer: chỉ xem, không có quyền bật DND.")

if time.time() < st.session_state.dnd_until:
    remain = int(st.session_state.dnd_until - time.time())
    st.warning(f"🔕 DND đang bật (còn {remain}s) — hệ thống chỉ ghi log, không phát cảnh báo.")
else:
    st.info("✅ Silent Mode đang hoạt động (không phát âm thanh).")

sample_events = [
    {"ts":"2025-10-02 10:01:05","exam_id":"E01","student":"HS01","event":"pose_right","severity":"YELLOW"},
    {"ts":"2025-10-02 10:01:06","exam_id":"E01","student":"HS01","event":"audio_ask","severity":"RED"},
    {"ts":"2025-10-02 10:03:20","exam_id":"E02","student":"HS02","event":"pose_down","severity":"YELLOW"},
]
df = pd.DataFrame(sample_events)
scope = st.session_state.auth_exam_scope
if scope:
    df = df[df["exam_id"] == scope]

st.subheader("📌 Sự kiện mới nhất")
def style_rows(row):
    color = {'RED':'#ffcccc','YELLOW':'#fff2cc','GREEN':'#ccffcc'}.get(row['severity'],'#f6f6f6')
    return [f'background-color: {color}']*len(row)
st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True, height=320)

@require_roles("admin")
def admin_config_panel():
    st.subheader("⚙️ Cấu hình hệ thống (Admin)")
    col1, col2 = st.columns(2)
    with col1:
        pitch_down = st.number_input("Ngưỡng Pitch cúi xuống (độ)", value=-15)
        yaw_side   = st.number_input("Ngưỡng Yaw quay ngang (độ)", value=20)
    with col2:
        fusion_red    = st.text_input("Rule RED", value="(audio_ask and pose_suspect) or (rf_detect and pose_suspect)")
        fusion_yellow = st.text_input("Rule YELLOW", value="pose_suspect or audio_ask or rf_detect")
    if st.button("💾 Lưu cấu hình"):
        st.success("Đã lưu (demo).")

@require_roles("admin")
def user_mgmt_panel():
    st.subheader("👤 Quản lý người dùng (Admin)")
    cols_show = ["user","role","exam_scope"]
    data_show = [{"user":u.get("user"),"role":u.get("role","viewer"),"exam_scope":u.get("exam_scope","-")} for u in USERS]
    st.dataframe(pd.DataFrame(data_show, columns=cols_show), use_container_width=True)

    st.markdown("### ➕ Thêm người dùng mới")
    with st.form("add_user_form", clear_on_submit=True):
        new_user = st.text_input("Tài khoản *").strip()
        new_pass = st.text_input("Mật khẩu *", type="password")
        new_role = st.selectbox("Vai trò *", ["admin","proctor","viewer"])
        new_scope = st.text_input("Phạm vi kỳ thi (exam_scope, tùy chọn)")
        submitted = st.form_submit_button("Thêm")
    if submitted:
        if not new_user or not new_pass:
            st.error("Vui lòng nhập đầy đủ tài khoản và mật khẩu.")
        elif new_user in [u["user"] for u in USERS]:
            st.error("Tài khoản đã tồn tại.")
        else:
            USERS.append({
                "user": new_user,
                "pass_sha256": sha256(new_pass),
                "role": new_role,
                **({"exam_scope": new_scope} if new_scope else {})
            })
            try:
                save_users(USERS)
                st.success(f"Đã tạo người dùng '{new_user}' với vai trò '{new_role}'.")
            except Exception as e:
                st.warning(f"Không lưu được users.json: {e}")
            st.rerun()

    st.markdown("### ✏️ Cập nhật / Xóa người dùng")
    if USERS:
        target = st.selectbox("Chọn tài khoản", [u["user"] for u in USERS])
        if target:
            rec = next((x for x in USERS if x["user"] == target), None)
            if rec:
                colA, colB = st.columns(2)
                with colA:
                    new_role2 = st.selectbox("Vai trò", ["admin","proctor","viewer"], index=["admin","proctor","viewer"].index(rec.get("role","viewer")))
                    new_scope2 = st.text_input("exam_scope", value=rec.get("exam_scope",""))
                    if st.button("💾 Lưu thay đổi"):
                        rec["role"] = new_role2
                        if new_scope2: rec["exam_scope"] = new_scope2
                        else: rec.pop("exam_scope", None)
                        try:
                            save_users(USERS)
                            st.success("Đã cập nhật người dùng.")
                        except Exception as e:
                            st.warning(f"Không lưu được users.json: {e}")
                        st.rerun()
                with colB:
                    st.markdown("Đặt lại mật khẩu:")
                    npw = st.text_input("Mật khẩu mới", type="password", key="reset_pw")
                    if st.button("🔑 Đặt lại mật khẩu"):
                        if not npw:
                            st.error("Vui lòng nhập mật khẩu mới.")
                        else:
                            rec["pass_sha256"] = sha256(npw)
                            try:
                                save_users(USERS)
                                st.success("Đã đặt lại mật khẩu.")
                            except Exception as e:
                                st.warning(f"Không lưu được users.json: {e}")
                            st.rerun()
                    st.markdown("---")
                    if st.button("🗑️ Xóa người dùng", type="primary"):
                        if rec["user"] == st.session_state.auth_user:
                            st.error("Không thể tự xóa chính mình.")
                        else:
                            USERS[:] = [u for u in USERS if u["user"] != rec["user"]]
                            try:
                                save_users(USERS)
                                st.success("Đã xóa người dùng.")
                            except Exception as e:
                                st.warning(f"Không lưu được users.json: {e}")
                            st.rerun()

with st.expander("Khu vực quản trị (Admin-only)"):
    if st.session_state.auth_role == "admin":
        admin_config_panel()
        st.divider()
        user_mgmt_panel()
    else:
        st.info("Bạn không có quyền admin.")

if st.session_state.auth_role in ["admin","proctor"]:
    st.subheader("🛡️ Bảng điều khiển giám thị")
    if df.empty:
        st.info("Không có sự kiện thuộc phạm vi của bạn.")
    else:
        idx = st.selectbox("Chọn dòng để ACK", options=list(df.index),
                           format_func=lambda i: f"{df.loc[i,'exam_id']} · {df.loc[i,'student']} · {df.loc[i,'event']}")
        if st.button("✅ ACK sự kiện"):
            st.success(f"Đã ACK dòng #{idx} (demo).")

st.subheader("👁️ Tổng quan rủi ro (Read-only)")
df_risk = pd.DataFrame([
    {"exam_id":"E01","student":"HS01","risk":7},
    {"exam_id":"E02","student":"HS02","risk":3},
])
if scope:
    df_risk = df_risk[df_risk["exam_id"] == scope]
st.dataframe(df_risk, use_container_width=True)

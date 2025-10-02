import streamlit as st, hashlib, time, pandas as pd

def sha256(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

# Demo user DB
USERS = [
    {"user":"admin1","pass_sha256":sha256("admin123"),"role":"admin"},
    {"user":"gv01","pass_sha256":sha256("proctor123"),"role":"proctor","exam_scope":"E01"},
    {"user":"view1","pass_sha256":sha256("viewer123"),"role":"viewer"}
]
USERMAP = {u["user"]:u for u in USERS}

for k,v in {"auth_ok":False,"auth_user":None,"auth_role":None,"auth_exam_scope":None,
            "auth_attempts":0,"auth_locked_until":0.0}.items():
    st.session_state.setdefault(k,v)

def login_form():
    st.sidebar.subheader("🔐 Đăng nhập")
    if time.time()<st.session_state.auth_locked_until:
        st.sidebar.error(f"Khóa {int(st.session_state.auth_locked_until-time.time())}s")
        return
    with st.sidebar.form("login"):
        u=st.text_input("User")
        p=st.text_input("Pass",type="password")
        ok=st.form_submit_button("Đăng nhập")
    if ok:
        rec=USERMAP.get(u)
        if rec and sha256(p)==rec["pass_sha256"]:
            st.session_state.auth_ok=True
            st.session_state.auth_user=u
            st.session_state.auth_role=rec.get("role","viewer")
            st.session_state.auth_exam_scope=rec.get("exam_scope")
            st.session_state.auth_attempts=0
            st.sidebar.success(f"Xin chào {u} ({st.session_state.auth_role})")
        else:
            st.session_state.auth_attempts+=1
            left=5-st.session_state.auth_attempts
            st.sidebar.error(f"Sai mật khẩu. Còn {left}")
            if st.session_state.auth_attempts>=5:
                st.session_state.auth_locked_until=time.time()+60

def logout_btn():
    if st.sidebar.button("🚪 Đăng xuất"):
        for k in ["auth_ok","auth_user","auth_role","auth_exam_scope"]: st.session_state[k]=None
        st.session_state.auth_ok=False

def require_roles(*roles):
    def deco(fn):
        def wrapped(*a,**kw):
            if not st.session_state.auth_ok: st.warning("Cần đăng nhập."); st.stop()
            if st.session_state.auth_role not in roles: st.error("Không đủ quyền."); st.stop()
            return fn(*a,**kw)
        return wrapped
    return deco

if not st.session_state.auth_ok:
    login_form(); st.stop()
else:
    st.sidebar.caption(f"Đăng nhập: {st.session_state.auth_user} ({st.session_state.auth_role})")
    if st.session_state.auth_exam_scope: st.sidebar.caption(f"Scope: {st.session_state.auth_exam_scope}")
    logout_btn()

st.title("📊 Exam Proctor Dashboard – RBAC Demo")

# ADMIN
@require_roles("admin")
def admin_panel():
    st.subheader("⚙️ Admin Config")
    pitch=st.number_input("Pitch ngưỡng",value=-15)
    yaw=st.number_input("Yaw ngưỡng",value=20)
    if st.button("💾 Lưu cấu hình"): st.success("Đã lưu (demo)")

if st.session_state.auth_role=="admin":
    with st.expander("Admin Panel"):
        admin_panel()

# PROCTOR
if st.session_state.auth_role in ["admin","proctor"]:
    st.subheader("🛡️ Giám thị")
    data=[
        {"ts":"2025-10-02 10:01","exam_id":"E01","student":"HS01","event":"pose_right","severity":"YELLOW"},
        {"ts":"2025-10-02 10:02","exam_id":"E01","student":"HS01","event":"audio_ask","severity":"RED"},
        {"ts":"2025-10-02 10:03","exam_id":"E02","student":"HS02","event":"pose_down","severity":"YELLOW"}
    ]
    df=pd.DataFrame(data)
    scope=st.session_state.auth_exam_scope
    if scope: df=df[df.exam_id==scope]
    st.dataframe(df,use_container_width=True)
    if not df.empty:
        idx=st.selectbox("Chọn dòng ACK",df.index)
        if st.button("✅ ACK"): st.success(f"Đã ACK {idx}")

# VIEWER
st.subheader("👁️ Viewer")
df2=pd.DataFrame([{"exam_id":"E01","student":"HS01","risk":7},
                  {"exam_id":"E02","student":"HS02","risk":3}])
scope=st.session_state.auth_exam_scope
if scope: df2=df2[df2.exam_id==scope]
st.dataframe(df2,use_container_width=True)

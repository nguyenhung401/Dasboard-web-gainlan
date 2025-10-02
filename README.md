# Exam Proctor Dashboard – RBAC + User Management
- Đăng nhập & phân quyền (admin/proctor/viewer)
- Quản lý người dùng **trực tiếp trên Dashboard** (admin-only): thêm/sửa/xóa, reset mật khẩu, đổi vai trò, gán exam_scope
- Lưu người dùng vào **users.json** (persist giữa các lần chạy)

## Chạy
```bash
pip install streamlit pandas
streamlit run app.py
```

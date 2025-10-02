# 📊 Exam Proctor Dashboard – RBAC

Demo Dashboard Streamlit có đăng nhập + phân quyền (Admin / Proctor / Viewer).

## Tài khoản demo
- admin1 / admin123 → admin
- gv01 / proctor123 → proctor (chỉ xem Exam E01)
- view1 / viewer123 → viewer (read-only)

## Chạy local
```bash
pip install -r requirements.txt
streamlit run app_rbac.py
```

## Deploy
- Push lên GitHub, deploy với Streamlit Cloud.
- Hoặc chạy trên Replit.

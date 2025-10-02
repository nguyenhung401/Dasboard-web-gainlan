# 📊 Exam Proctor Dashboard – Silent Mode

Dự án mẫu cho **đề tài khoa học kỹ thuật**:  
Hệ thống Dashboard giám thị (Streamlit) để phát hiện gian lận trong phòng thi.  
- **Silent Mode**: chỉ hiển thị cảnh báo, không phát âm thanh → tránh làm ồn học sinh.  
- **Do Not Disturb (DND)**: tạm dừng cảnh báo khi giám thị phổ biến nội quy.  
- **Giao diện trực quan**: hiển thị sự kiện theo thời gian, đánh dấu màu theo mức độ (RED, YELLOW, GREEN).

---

## 🚀 Chạy trên máy cá nhân

### Cài đặt
```bash
git clone https://github.com/<username>/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
```

### Chạy app
```bash
streamlit run app.py
```

Mở trình duyệt tại: [http://localhost:8501](http://localhost:8501)

---

## ☁️ Deploy Online với Streamlit Cloud

1. Push code này lên GitHub (public repo).  
2. Vào [https://share.streamlit.io](https://share.streamlit.io) → đăng nhập bằng GitHub.  
3. Chọn repo + branch, chọn file `app.py` để chạy.  
4. Hệ thống sẽ tự tạo link public dạng:  
   ```
   https://<username>-<repo>-<branch>.streamlit.app
   ```

---

## 📂 Cấu trúc repo
```
repo-name/
 ├── app.py              # Code Dashboard (Streamlit)
 ├── requirements.txt    # Thư viện cần thiết (streamlit, pandas)
 └── README.md           # Hướng dẫn
```

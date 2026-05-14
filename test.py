from ultralytics import YOLO

file_path = r"C:\Users\Lenovo\Downloads\DATN\backend\weights\yolov8n.pt"

try:
    # Cố gắng load file
    model = YOLO(file_path)
    
    print("✅ Đây là file YOLO hợp lệ!")
    print(f"👉 Nhiệm vụ của mô hình (Task): {model.task}") # Thường là 'detect', 'segment', 'classify'
    print(f"👉 Danh sách các class nhận diện được: {model.names}")
    
except Exception as e:
    print("❌ Đây KHÔNG phải là file YOLO hợp lệ, hoặc file đã bị hỏng.")
    print(f"Chi tiết lỗi: {e}")
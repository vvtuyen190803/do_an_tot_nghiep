# import cv2, numpy as np, torch, os, sqlite3
# from ultralytics import YOLO
# from ultralytics.solutions import speed_estimation

# # Map loại xe theo COCO dataset[cite: 17]
# VEHICLE_CLASSES = {2: "Ô tô", 3: "Xe máy", 5: "Xe buýt", 7: "Xe tải"}

# def run(args):
#     try:
#         # Nạp 2 model: Detect xe và Detect biển số[cite: 17]
#         lp_model = YOLO(args.get('lp_detect_model', 'weights/yolov8_plate_detect.pt'))
#         cap = cv2.VideoCapture(str(args['source']))
#         W, H = int(cap.get(3)), int(cap.get(4))
        
#         # Output video phân tích[cite: 17]
#         out_v = cv2.VideoWriter(args['output_path'], cv2.VideoWriter_fourcc(*'mp4v'), cap.get(5) or 30.0, (W, H))

#         # Vạch đo tốc độ[cite: 17]
#         line_pts = [(0, int(H/2)), (W, int(H/2))]
        
#         speed_obj = speed_estimation.SpeedEstimator(
#             model=args['yolo_model'], 
#             region=line_pts, 
#             show=False,
#             classes=args.get('classes', [2, 3, 5, 7]), 
#             conf=args['conf'],
#             device=0 if torch.cuda.is_available() else 'cpu',
#             meter_per_pixel=args.get('meter_per_pixel', 0.015)
#         )

#         saved_v = set(); waiting = {}; v_dir = "temp_results/violations"
#         os.makedirs(v_dir, exist_ok=True)

#         while cap.isOpened():
#             success, frame = cap.read()
#             if not success: break
#             original = frame.copy()
            
#             # Xử lý frame qua AI[cite: 17]
#             res = speed_obj.process(frame)
#             spd_data = getattr(speed_obj, 'spd', {})

#             # --- VẼ ID LÊN TẤT CẢ CÁC XE TRÊN VIDEO ---[cite: 17]
#             results = speed_obj.model.predictor.results[0]
#             if results.boxes.id is not None:
#                 boxes = results.boxes.xyxy.cpu().numpy().astype(int)
#                 ids = results.boxes.id.cpu().numpy().astype(int)
#                 for box, obj_id in zip(boxes, ids):
#                     cv2.putText(frame, f"ID:{obj_id}", (box[0], box[1] - 10),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

#             # --- LOGIC XỬ LÝ VI PHẠM ---[cite: 17, 18]
#             for obj_id, spd in spd_data.items():
#                 if spd > float(args['speed_limit']) and obj_id not in saved_v:
#                     waiting[obj_id] = waiting.get(obj_id, 0) + 1
#                     if waiting[obj_id] >= 7:
#                         try:
#                             ids_check = results.boxes.id.cpu().numpy().astype(int)
#                             if obj_id in ids_check:
#                                 idx = np.where(ids_check == obj_id)[0][0]
#                                 b = results.boxes.xyxy[idx].cpu().numpy().astype(int)
#                                 v_type = VEHICLE_CLASSES.get(int(results.boxes.cls[idx]), "Khac")
                                
#                                 # 1. Cắt ảnh xe vi phạm[cite: 17]
#                                 crop_xe = original[max(0, b[1]-20):min(H, b[3]+100), max(0, b[0]-50):min(W, b[2]+50)]
#                                 xe_name = f"XE_{v_type}_ID{obj_id}_{int(spd)}kmh.jpg"
#                                 xe_path = os.path.join(v_dir, xe_name)
#                                 cv2.imwrite(xe_path, crop_xe)

#                                 # 2. Nhận diện và cắt ảnh biển số (Fix lỗi không hiện biển)[cite: 17]
#                                 lp_res = lp_model(crop_xe, conf=0.2, verbose=False)[0] 
#                                 lp_url = ""
#                                 if len(lp_res.boxes) > 0:
#                                     lpb = lp_res.boxes.xyxy[0].cpu().numpy().astype(int)
#                                     pad = 15 
#                                     crop_lp = crop_xe[max(0, lpb[1]-pad):min(crop_xe.shape[0], lpb[3]+pad), 
#                                                       max(0, lpb[0]-pad):min(crop_xe.shape[1], lpb[2]+pad)]
#                                     lp_name = f"BIENSO_ID{obj_id}_{int(spd)}kmh.jpg"
#                                     lp_path = os.path.join(v_dir, lp_name)
#                                     cv2.imwrite(lp_path, crop_lp)
#                                     lp_url = f"http://localhost:8000/results/violations/{lp_name}"

#                                 # 3. Lưu vào Database
#                                 conn = sqlite3.connect(args['db_path'])
#                                 xe_url = f"http://localhost:8000/results/violations/{xe_name}"
#                                 conn.execute('''INSERT INTO violations (analysis_id, vehicle_type, speed, image_xe_url, image_bienso_url) 
#                                                 VALUES (?, ?, ?, ?, ?)''', (args['analysis_id'], v_type, int(spd), xe_url, lp_url))
#                                 conn.commit(); conn.close()
#                                 saved_v.add(obj_id)
#                         except: pass
            
#             # Ghi frame vào video kết quả[cite: 17]
#             out_v.write(frame)
#     finally:
#         if cap: cap.release()
#         if out_v: out_v.release()

# def track(args): return run(args)

import cv2, numpy as np, torch, os, sqlite3, base64
from ultralytics import YOLO
from ultralytics.solutions import speed_estimation

# Map loại xe theo COCO dataset phục vụ lưu Database
VEHICLE_CLASSES = {2: "Ô tô", 3: "Xe máy", 5: "Xe buýt", 7: "Xe tải"}

def image_to_base64(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def run(args):
    try:
        # Nạp model biển số từ cấu hình backend
        lp_model = YOLO(args.get('lp_detect_model', 'weights/yolov8_plate_detect.pt'))
        if torch.cuda.is_available():
            lp_model.to('cuda')
        cap = cv2.VideoCapture(str(args['source']))
        W, H = int(cap.get(3)), int(cap.get(4))
        
        # Cấu hình video đầu ra
        out_v = cv2.VideoWriter(args['output_path'], cv2.VideoWriter_fourcc(*'mp4v'), cap.get(5) or 30.0, (W, H))

        # Vạch đo tốc độ mặc định
        line_pts = [(0, int(H/2)), (W, int(H/2))]
        
        speed_obj = speed_estimation.SpeedEstimator(
            model=args['yolo_model'], 
            region=line_pts, 
            show=False,
            classes=args.get('classes', [2, 3, 5, 7]), 
            conf=args['conf'],
            device=0 if torch.cuda.is_available() else 'cpu',
            meter_per_pixel=args.get('meter_per_pixel', 0.015),
            tracker='bytetrack.yaml'
        )

        saved_v = set(); waiting = {}; v_dir = "temp_results/violations"
        os.makedirs(v_dir, exist_ok=True)

        while cap.isOpened():
            success, frame = cap.read()
            if not success: break
            original = frame.copy()
            
            # Xử lý frame qua mô hình tốc độ
            res = speed_obj.process(frame)
            spd_data = getattr(speed_obj, 'spd', {})

            # --- CẬP NHẬT: VẼ ID VÀ MÃ LỚP (CLS) LÊN VIDEO ---
            results = speed_obj.model.predictor.results[0]
            if results.boxes.id is not None:
                boxes = results.boxes.xyxy.cpu().numpy().astype(int)
                ids = results.boxes.id.cpu().numpy().astype(int)
                clss = results.boxes.cls.cpu().numpy().astype(int) # Lấy mã lớp xe
                
                for box, obj_id, cls_id in zip(boxes, ids, clss):
                    current_spd = spd_data.get(obj_id, 0)
                    box_color = (0, 0, 255) if current_spd > float(args['speed_limit']) else (0, 255, 0)
                    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), box_color, 2)
                    # Hiển thị dạng: ID:1 C:3 (C:3 nghĩa là xe máy theo COCO)
                    display_text = f"ID:{obj_id} C:{cls_id}"
                    cv2.putText(frame, display_text, (box[0], max(35, box[1] - 35)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            # --- LOGIC XỬ LÝ VI PHẠM ---
            for obj_id, spd in spd_data.items():
                if spd > float(args['speed_limit']) and obj_id not in saved_v:
                    waiting[obj_id] = waiting.get(obj_id, 0) + 1
                    if waiting[obj_id] >= 7:
                        try:
                            ids_check = results.boxes.id.cpu().numpy().astype(int)
                            if obj_id in ids_check:
                                idx = np.where(ids_check == obj_id)[0][0]
                                b = results.boxes.xyxy[idx].cpu().numpy().astype(int)
                                v_type = VEHICLE_CLASSES.get(int(results.boxes.cls[idx]), "Khac")
                                
                                # Cắt ảnh xe
                                crop_xe = original[max(0, b[1]-20):min(H, b[3]+100), max(0, b[0]-50):min(W, b[2]+50)]
                                xe_name = f"XE_{v_type}_ID{obj_id}_{int(spd)}kmh.jpg"
                                xe_path = os.path.join(v_dir, xe_name)
                                cv2.imwrite(xe_path, crop_xe)

                                # Nhận diện biển số 
                                lp_res = lp_model(crop_xe, conf=0.2, verbose=False)[0] 
                                lp_base64 = ""
                                if len(lp_res.boxes) > 0:
                                    lpb = lp_res.boxes.xyxy[0].cpu().numpy().astype(int)
                                    pad = 15 
                                    crop_lp = crop_xe[max(0, lpb[1]-pad):min(crop_xe.shape[0], lpb[3]+pad), 
                                                      max(0, lpb[0]-pad):min(crop_xe.shape[1], lpb[2]+pad)]
                                    lp_name = f"BIENSO_ID{obj_id}_{int(spd)}kmh.jpg"
                                    lp_path = os.path.join(v_dir, lp_name)
                                    cv2.imwrite(lp_path, crop_lp)
                                    lp_base64 = image_to_base64(lp_path)

                                # Lưu thông tin vào Database
                                conn = sqlite3.connect(args['db_path'])
                                xe_base64 = image_to_base64(xe_path)
                                conn.execute('''INSERT INTO violations (analysis_id, vehicle_type, speed, image_xe_url, image_bienso_url) 
                                                VALUES (?, ?, ?, ?, ?)''', (args['analysis_id'], v_type, int(spd), xe_base64, lp_base64))
                                conn.commit(); conn.close()
                                saved_v.add(obj_id)
                        except: pass
            
            # Ghi frame đã xử lý vào file video
            out_v.write(frame)
    finally:
        if cap: cap.release()
        if out_v: out_v.release()

def track(args): return run(args)
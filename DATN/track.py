import cv2, numpy as np, torch, os, sqlite3
from ultralytics import YOLO
from ultralytics.solutions import speed_estimation

# Map loại xe theo COCO dataset
VEHICLE_CLASSES = {2: "Ô tô", 3: "Xe máy", 5: "Xe buýt", 7: "Xe tải"}

def run(args):
    try:
        # Nạp 2 model chính: Detect xe và Detect biển số
        lp_model = YOLO(args.get('weights/yolov8n.pt', 'weights/yolov8_plate_detect.pt'))
        cap = cv2.VideoCapture(str(args['source']))
        W, H = int(cap.get(3)), int(cap.get(4))
        
        # Output video phân tích
        out_v = cv2.VideoWriter(args['output_path'], cv2.VideoWriter_fourcc(*'mp4v'), cap.get(5) or 30.0, (W, H))

        # Vạch đo tốc độ (mặc định giữa màn hình)[cite: 11]
        line_pts = [(0, int(H/2)), (W, int(H/2))]
        
        speed_obj = speed_estimation.SpeedEstimator(
            model=args['yolo_model'], 
            region=line_pts, 
            show=False,
            classes=args.get('classes', [2, 3, 5, 7]), 
            conf=args['conf'],
            device=0 if torch.cuda.is_available() else 'cpu',
            meter_per_pixel=args.get('meter_per_pixel', 0.015)
        )

        saved_v = set(); waiting = {}; v_dir = "temp_results/violations"
        os.makedirs(v_dir, exist_ok=True)

        while cap.isOpened():
            success, frame = cap.read()
            if not success: break
            original = frame.copy()
            res = speed_obj.process(frame)
            spd_data = getattr(speed_obj, 'spd', {})

            for obj_id, spd in spd_data.items():
                if spd > float(args['speed_limit']) and obj_id not in saved_v:
                    waiting[obj_id] = waiting.get(obj_id, 0) + 1
                    # Chờ 7 khung hình để xe đi vào vùng rõ nhất[cite: 11]
                    if waiting[obj_id] >= 7:
                        try:
                            r = speed_obj.model.predictor.results[0]
                            if r.boxes.id is not None:
                                ids = r.boxes.id.cpu().numpy().astype(int)
                                if obj_id in ids:
                                    idx = np.where(ids == obj_id)[0][0]
                                    b = r.boxes.xyxy[idx].cpu().numpy().astype(int)
                                    v_type = VEHICLE_CLASSES.get(int(r.boxes.cls[idx]), "Khac")
                                    
                                    # 1. Cắt ảnh toàn bộ xe vi phạm[cite: 11]
                                    crop_xe = original[max(0, b[1]-20):min(H, b[3]+100), max(0, b[0]-50):min(W, b[2]+50)]
                                    xe_name = f"XE_{v_type}_ID{obj_id}_{int(spd)}kmh.jpg"
                                    xe_path = os.path.join(v_dir, xe_name)
                                    cv2.imwrite(xe_path, crop_xe)

                                    # 2. Detect và cắt ảnh biển số (nếu có)[cite: 11]
                                    lp_res = lp_model(crop_xe, conf=0.4, verbose=False)[0]
                                    lp_url = ""
                                    if len(lp_res.boxes) > 0:
                                        lpb = lp_res.boxes.xyxy[0].cpu().numpy().astype(int)
                                        pad = 15 
                                        crop_lp = crop_xe[max(0, lpb[1]-pad):min(crop_xe.shape[0], lpb[3]+pad), max(0, lpb[0]-pad):min(crop_xe.shape[1], lpb[2]+pad)]
                                        lp_name = f"BIENSO_ID{obj_id}_{int(spd)}kmh.jpg"
                                        lp_path = os.path.join(v_dir, lp_name)
                                        cv2.imwrite(lp_path, crop_lp)
                                        lp_url = f"http://localhost:8000/results/violations/{lp_name}"

                                    # 3. Lưu vào SQLite (Bỏ cột plate_text)[cite: 10, 11]
                                    conn = sqlite3.connect(args['db_path'])
                                    xe_url = f"http://localhost:8000/results/violations/{xe_name}"
                                    conn.execute('''INSERT INTO violations (analysis_id, vehicle_type, speed, image_xe_url, image_bienso_url) 
                                                    VALUES (?, ?, ?, ?, ?)''', (args['analysis_id'], v_type, int(spd), xe_url, lp_url))
                                    conn.commit(); conn.close()
                                    saved_v.add(obj_id)
                        except: pass
            out_v.write(res.plot_im if hasattr(res, 'plot_im') else frame)
    finally:
        if cap: cap.release()
        if out_v: out_v.release()

def track(args): return run(args)
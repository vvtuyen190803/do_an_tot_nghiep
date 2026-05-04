from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn, shutil, os, json, subprocess, time, sqlite3

app = FastAPI(title="Hệ thống phát hiện phương tiện vi phạm quá tốc độ YOLOv8")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

VIOLATION_DIR, UPLOAD_DIR, RESULT_DIR = "temp_results/violations", "temp_uploads", "temp_results"
DB_PATH = "traffic_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 1. Bảng người dùng (Thêm mới)
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT UNIQUE, phone TEXT, password TEXT)''')
    # 2. Bảng lịch sử phiên phân tích
    cursor.execute('''CREATE TABLE IF NOT EXISTS analysis_history 
        (id INTEGER PRIMARY KEY, filename TEXT, video_url TEXT, speed_limit REAL, timestamp TEXT)''')
    # 3. Bảng danh sách xe vi phạm
    cursor.execute('''CREATE TABLE IF NOT EXISTS violations 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, analysis_id INTEGER, vehicle_type TEXT, 
         speed REAL, image_xe_url TEXT, image_bienso_url TEXT)''')
    conn.commit(); conn.close()

def startup_cleanup():
    for folder in [UPLOAD_DIR, VIOLATION_DIR, RESULT_DIR]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                try: os.unlink(os.path.join(folder, f))
                except: pass

os.makedirs(UPLOAD_DIR, exist_ok=True); os.makedirs(RESULT_DIR, exist_ok=True); os.makedirs(VIOLATION_DIR, exist_ok=True)
app.mount("/results", StaticFiles(directory=RESULT_DIR), name="results")

# --- MODEL NHẬN DỮ LIỆU ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    password: str

class LoginRequest(BaseModel):
    email: str # Sử dụng email để đăng nhập
    password: str

# --- API ĐĂNG KÝ ---
@app.post("/api/register")
async def register(user: RegisterRequest):
    conn = sqlite3.connect(DB_PATH)
    try:
        # Kiểm tra email tồn tại
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")
        
        conn.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                     (user.username, user.email, user.phone, user.password))
        conn.commit()
        return {"status": "success", "message": "Đăng ký thành công!"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- API ĐĂNG NHẬP ---
@app.post("/api/login")
async def login(credentials: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    # Kiểm tra email và mật khẩu trong DB
    user = conn.execute("SELECT username FROM users WHERE email = ? AND password = ?", 
                        (credentials.email, credentials.password)).fetchone()
    conn.close()
    
    if user:
        return {"status": "success", "token": "eyJhbGciOiJIUzI1NiJ9.user_verified.sig", "username": user[0]}
    else:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")

# --- PHẦN ANALYZE VÀ HISTORY GIỮ NGUYÊN[cite: 12] ---
@app.post("/api/analyze-speed")
async def analyze_speed(video: UploadFile = File(...), points: str = Form(...), speed_limit: float = Form(...), meter_per_pixel: float = Form(...)):
    unique_id = int(time.time())
    safe_filename = f"{unique_id}_{video.filename}"
    temp_path = f"{UPLOAD_DIR}/{safe_filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(video.file, buffer)
    raw_v = f"{RESULT_DIR}/raw_{safe_filename}"
    web_v = f"{RESULT_DIR}/web_{safe_filename}"
    ai_config = {
        'analysis_id': unique_id, 'db_path': DB_PATH, 'source': temp_path, 
        'points': json.loads(points), 'speed_limit': speed_limit, 'meter_per_pixel': meter_per_pixel, 
        'yolo_model': 'weights/yolov8n.pt', 'lp_detect_model': 'weights/yolov8_plate_detect.pt',
        'conf': 0.25, 'device': 0, 'classes': [2, 3, 5, 7], 'output_path': raw_v
    }
    try:
        from scenario.track import run
        run(ai_config)
        subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-vcodec", "libx264", "-crf", "28", web_v])
        conn = sqlite3.connect(DB_PATH)
        timestamp = time.strftime("%H:%M:%S - %d/%m/%Y")
        video_url = f"http://localhost:8000/results/{os.path.basename(web_v)}"
        conn.execute('INSERT INTO analysis_history VALUES (?,?,?,?,?)', (unique_id, video.filename, video_url, speed_limit, timestamp))
        conn.commit(); conn.close()
        return {"id": unique_id, "video_url": video_url, "filename": video.filename, "speed_limit": speed_limit, "timestamp": timestamp}
    except Exception as e: return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    data = [dict(row) for row in conn.execute('SELECT * FROM analysis_history ORDER BY id DESC').fetchall()]
    conn.close(); return data

@app.get("/api/violations")
async def get_violations():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    data = [dict(row) for row in conn.execute('SELECT * FROM violations ORDER BY id DESC').fetchall()]
    conn.close(); return data

if __name__ == "__main__":
    init_db(); startup_cleanup()
    uvicorn.run(app, host="0.0.0.0", port=8000)
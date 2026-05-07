from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn, shutil, os, json, subprocess, time, sqlite3, asyncio, sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="Hệ thống phát hiện phương tiện vi phạm quá tốc độ YOLOv8")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

VIOLATION_DIR, UPLOAD_DIR, RESULT_DIR = "temp_results/violations", "temp_uploads", "temp_results"
DB_PATH = "traffic_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT UNIQUE, phone TEXT, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS analysis_history 
        (id INTEGER PRIMARY KEY, filename TEXT, video_url TEXT, speed_limit REAL, timestamp TEXT)''')
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

# Model nhận dữ liệu
class RegisterRequest(BaseModel):
    username: str; email: str; phone: str; password: str

class LoginRequest(BaseModel):
    email: str; password: str

@app.post("/api/register")
async def register(user: RegisterRequest):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
                     (user.username, user.email, user.phone, user.password))
        conn.commit(); return {"status": "success"}
    except: raise HTTPException(status_code=400, detail="Email đã tồn tại!")
    finally: conn.close()

@app.post("/api/login")
async def login(credentials: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    user = conn.execute("SELECT username FROM users WHERE email = ? AND password = ?", 
                        (credentials.email, credentials.password)).fetchone()
    conn.close()
    if user: return {"status": "success", "token": "verified_token", "username": user[0]}
    raise HTTPException(status_code=401)

@app.post("/api/analyze-speed")
def analyze_speed(video: UploadFile = File(...), points: str = Form(...), speed_limit: float = Form(...), meter_per_pixel: float = Form(...)):
    unique_id = int(time.time())
    safe_filename = f"{unique_id}_{video.filename}"
    temp_path = f"{UPLOAD_DIR}/{safe_filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(video.file, buffer)
    
    raw_v = f"{RESULT_DIR}/raw_{safe_filename}"
    web_v = f"{RESULT_DIR}/web_{safe_filename}"
    
    # Cập nhật đường dẫn model chính xác cho folder backend[cite: 18]
    ai_config = {
        'analysis_id': unique_id, 'db_path': DB_PATH, 'source': temp_path, 
        'points': json.loads(points), 'speed_limit': speed_limit, 'meter_per_pixel': meter_per_pixel, 
        'yolo_model': 'weights/yolov8n.pt', 
        'lp_detect_model': 'weights/yolov8_plate_detect.pt',
        'conf': 0.25, 'device': 0, 'classes': [2, 3, 5, 7], 'output_path': raw_v
    }
    
    try:
        from track import run # Import trực tiếp vì cùng folder backend[cite: 18]
        run(ai_config)
        subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-vcodec", "h264_nvenc", "-cq", "28", web_v])
        
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

# --- API XÓA TOÀN BỘ DỮ LIỆU ---
@app.delete("/api/clear-data")
async def clear_data():
    try:
        # 1. Xóa dữ liệu trong Database
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM violations")
        conn.execute("DELETE FROM analysis_history")
        conn.commit()
        conn.close()
        
        # 2. Xóa các file vật lý trong folder[cite: 15]
        for folder in [UPLOAD_DIR, VIOLATION_DIR, RESULT_DIR]:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    try: os.unlink(os.path.join(folder, f))
                    except: pass
                    
        return {"status": "success", "message": "Đã xóa sạch dữ liệu!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    init_db(); startup_cleanup()
    uvicorn.run(app, host="0.0.0.0", port=8000)
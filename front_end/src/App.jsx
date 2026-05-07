import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';

// --- COMPONENT XÁC THỰC (Gồm Đăng nhập & Đăng ký) ---
const AuthScreen = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({
    username: '', email: '', phone: '', password: '', confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [successDialog, setSuccessDialog] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (isRegister) {
      if (formData.password !== formData.confirmPassword) return setError("Mật khẩu nhập lại không khớp!");
      try {
        const res = await axios.post("http://localhost:8000/api/register", {
          username: formData.username,
          email: formData.email,
          phone: formData.phone,
          password: formData.password
        });
        if (res.data.status === "success") {
          setSuccessDialog({
            title: "Đăng Ký Thành Công!",
            message: "Tài khoản của bạn đã được tạo thành công. Mời bạn đăng nhập.",
            onConfirm: () => {
              setSuccessDialog(null);
              setIsRegister(false);
            }
          });
        }
      } catch (err) { setError(err.response?.data?.detail || "Lỗi đăng ký!"); }
    } else {
      try {
        const res = await axios.post("http://localhost:8000/api/login", {
          email: formData.email,
          password: formData.password
        });
        localStorage.setItem('jwt_token', res.data.token);
        setSuccessDialog({
          title: "Đăng Nhập Thành Công!",
          message: "Chào mừng bạn đến với hệ thống giám sát giao thông.",
          onConfirm: () => {
            setSuccessDialog(null);
            onLogin();
          }
        });
      } catch (err) { setError("Email hoặc mật khẩu không chính xác!"); }
    }
  };

  return (
    <div className="container-fluid min-vh-100 d-flex align-items-center justify-content-center" style={{ backgroundColor: '#cfd8dc' }}>
      <div className="card shadow-lg border-0 rounded-4" style={{ width: '450px', backgroundColor: '#eceff1' }}>
        <div className="card-body p-5">
          <div className="text-center mb-4">
            <div className="display-4 mb-2">🚦</div>
            <h3 className="fw-bold text-primary">{isRegister ? "ĐĂNG KÝ HỆ THỐNG" : "ĐĂNG NHẬP HỆ THỐNG"}</h3>
          </div>
          <form onSubmit={handleSubmit}>
            {isRegister && (
              <>
                <div className="mb-3">
                  <label className="fw-bold text-secondary small mb-1">Tên hiển thị</label>
                  <input type="text" className="form-control" onChange={e => setFormData({ ...formData, username: e.target.value })} required />
                </div>
                <div className="mb-3">
                  <label className="fw-bold text-secondary small mb-1">Số điện thoại</label>
                  <input type="text" className="form-control" onChange={e => setFormData({ ...formData, phone: e.target.value })} required />
                </div>
              </>
            )}
            <div className="mb-3">
              <label className="fw-bold text-secondary small mb-1">Email đăng nhập</label>
              <input type="email" className="form-control" onChange={e => setFormData({ ...formData, email: e.target.value })} required />
            </div>
            <div className="mb-3">
              <label className="fw-bold text-secondary small mb-1">Mật khẩu</label>
              <input type="password" className="form-control" onChange={e => setFormData({ ...formData, password: e.target.value })} required />
            </div>
            {isRegister && (
              <div className="mb-3">
                <label className="fw-bold text-secondary small mb-1">Nhập lại mật khẩu</label>
                <input type="password" className="form-control" onChange={e => setFormData({ ...formData, confirmPassword: e.target.value })} required />
              </div>
            )}

            {error && <div className="alert alert-danger py-2 small text-center">{error}</div>}

            <button type="submit" className="btn btn-primary btn-lg w-100 fw-bold shadow-sm mt-2">
              {isRegister ? "TẠO TÀI KHOẢN" : "VÀO HỆ THỐNG"}
            </button>
            <div className="text-center mt-4">
              <span className="text-muted small" style={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => { setIsRegister(!isRegister); setError(''); }}>
                {isRegister ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Đăng ký ngay"}
              </span>
            </div>
          </form>
        </div>
      </div>

      {/* MODAL THÔNG BÁO THÀNH CÔNG */}
      {successDialog && (
        <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content border-0 rounded-4 shadow-lg text-center p-4">
              <div className="modal-body">
                <div className="display-1 mb-3">✅</div>
                <h4 className="fw-bold text-primary mb-3">{successDialog.title}</h4>
                <p className="text-secondary mb-4">{successDialog.message}</p>
                <button className="btn btn-primary btn-lg px-5 fw-bold rounded-pill shadow-sm" onClick={successDialog.onConfirm}>
                  OK, TIẾP TỤC
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- COMPONENT NAVIGATION (Giữ nguyên cấu trúc cũ) ---
const Navigation = ({ onLogout }) => {
  const location = useLocation();
  return (
    <nav className="navbar navbar-expand-lg navbar-light mb-4 shadow-sm border-bottom" style={{ backgroundColor: '#eceff1' }}>
      <div className="container-fluid px-4">
        <span className="navbar-brand fw-bold text-primary fs-4">🚦 HỆ THỐNG GIÁM SÁT GIAO THÔNG</span>
        <div className="collapse navbar-collapse d-flex justify-content-between">
          <ul className="navbar-nav ms-4">
            <li className="nav-item me-3">
              <Link className={`nav-link fw-bold px-3 rounded ${location.pathname === '/' ? 'bg-primary text-white shadow-sm' : 'text-secondary'}`} to="/">📹 GIÁM SÁT TRỰC TIẾP</Link>
            </li>
            <li className="nav-item">
              <Link className={`nav-link fw-bold px-3 rounded ${location.pathname === '/history' ? 'bg-primary text-white shadow-sm' : 'text-secondary'}`} to="/history">📜 DANH SÁCH PHƯƠNG TIỆN VI PHẠM</Link>
            </li>
          </ul>
          <button className="btn btn-outline-danger fw-bold shadow-sm px-4" onClick={onLogout}>Đăng xuất 🚪</button>
        </div>
      </div>
    </nav>
  );
};

// --- COMPONENT CHÍNH (Bảo toàn 100% logic giám sát cũ) ---
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('jwt_token'));
  const [videoFile, setVideoFile] = useState(null); // Biến lưu file video để xem trước
  const [meterPerPixel, setMeterPerPixel] = useState(0.035);
  const [speedLimit, setSpeedLimit] = useState(60);
  const [status, setStatus] = useState("");
  const [resultVideoUrl, setResultVideoUrl] = useState(null);
  const [history, setHistory] = useState([]);
  const [violations, setViolations] = useState([]);
  const [selectedImg, setSelectedImg] = useState(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState(null);

  const getAuthHeader = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('jwt_token')}` } });
  const handleLogout = () => { localStorage.removeItem('jwt_token'); setIsAuthenticated(false); };

  const syncData = async () => {
    try {
      const [histRes, violRes] = await Promise.all([
        axios.get("http://localhost:8000/api/history", getAuthHeader()),
        axios.get("http://localhost:8000/api/violations", getAuthHeader())
      ]);
      setHistory(histRes.data);
      setViolations(violRes.data);
    } catch (err) { console.error("Lỗi đồng bộ"); }
  };

  useEffect(() => { if (isAuthenticated) syncData(); }, [isAuthenticated]);

  const handleClearData = async () => {
    if (window.confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử vi phạm không?")) {
      try {
        await axios.delete("http://localhost:8000/api/clear-data", getAuthHeader());
        alert("Đã xóa dữ liệu thành công!");
        await syncData(); // Tải lại danh sách trống
      } catch (err) {
        alert("Lỗi khi xóa dữ liệu!");
      }
    }
  };
  // Hàm xử lý khi chọn file từ folder
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file); // Lưu file vào state
      setResultVideoUrl(null); // Xóa video đã xử lý cũ nếu có
      setStatus(""); // Reset trạng thái
    }
  };

  const handleDownloadBoth = async () => {
    if (!selectedImg) return;
    
    try {
      // Mở hộp thoại để người dùng chọn thư mục lưu
      const dirHandle = await window.showDirectoryPicker({ mode: 'readwrite' });

      // Hàm phụ trợ ghi file base64 vào thư mục đã chọn
      const saveBase64ToDir = async (base64Data, fileName) => {
        const byteString = atob(base64Data);
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
          ia[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([ab], { type: 'image/jpeg' });

        const fileHandle = await dirHandle.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
      };

      // Lưu ảnh xe
      await saveBase64ToDir(selectedImg.image_xe_url, `vi_pham_${selectedImg.id}_xe.jpg`);
      
      // Lưu ảnh biển số nếu có
      if (selectedImg.image_bienso_url) {
        await saveBase64ToDir(selectedImg.image_bienso_url, `vi_pham_${selectedImg.id}_bienso.jpg`);
      }

      alert("✅ Đã lưu thành công các ảnh vào thư mục bạn chọn!");
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error("Lỗi khi lưu file:", error);
        alert("❌ Trình duyệt không hỗ trợ tính năng này hoặc có lỗi xảy ra.");
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoFile) return; // Sử dụng videoFile trực tiếp từ state
    setStatus("⏳ Hệ thống (GPU RTX 3050) đang phân tích...");

    const formData = new FormData();
    formData.append("video", videoFile);
    formData.append("points", "[]");
    formData.append("meter_per_pixel", meterPerPixel);
    formData.append("speed_limit", speedLimit);

    try {
      const res = await axios.post("http://localhost:8000/api/analyze-speed", formData, getAuthHeader());
      setResultVideoUrl(res.data.video_url);
      setStatus("✅ Phân tích hoàn tất!");
      await syncData();
    } catch (err) { setStatus("❌ Lỗi Server AI!"); }
  };

  if (!isAuthenticated) return <AuthScreen onLogin={() => setIsAuthenticated(true)} />;

  return (
    <Router>
      <div className="container-fluid min-vh-100 p-0 pb-5" style={{ backgroundColor: '#cfd8dc' }}>
        <Navigation onLogout={handleLogout} />
        <div className="container-fluid px-4">
          <Routes>
            <Route path="/" element={
              <div className="row g-4">
                {/* --- CỘT TRÁI: ĐIỀU KHIỂN --- */}
                <div className="col-lg-4">
                  <div className="card shadow border-0 rounded-3 p-4 bg-white">
                    <h5 className="fw-bold mb-4 text-primary">⚙️ Cấu hình Phân tích AI</h5>
                    <form onSubmit={handleSubmit}>
                      <div className="mb-4">
                        <label className="fw-bold text-secondary mb-2 small">1. Tải lên Video Camera</label>
                        {/* Thêm onChange để gọi hàm preview */}
                        <input type="file" id="videoInput" className="form-control" accept="video/*" onChange={handleFileChange} />
                      </div>
                      <div className="mb-4">
                        <label className="fw-bold text-secondary mb-2 small">2. Tỷ lệ Camera (m/px)</label>
                        <input
                          type="number"
                          step="0.0001"
                          min="0.0001"
                          className="form-control text-center fw-bold"
                          value={meterPerPixel}
                          onChange={e => setMeterPerPixel(e.target.value)}
                        />
                      </div>
                      <div className="mb-4">
                        <div className="d-flex justify-content-between mb-2">
                          <label className="fw-bold text-danger small">3. Ngưỡng Vi Phạm</label>
                          <span className="badge bg-danger fs-6">{speedLimit} km/h</span>
                        </div>
                        <input type="range" className="form-range" min="0" max="120" value={speedLimit} onChange={e => setSpeedLimit(e.target.value)} />
                      </div>
                      <button type="submit" className="btn btn-primary btn-lg w-100 fw-bold shadow">🚀 BẮT ĐẦU GIÁM SÁT</button>
                    </form>
                    {status && <div className="alert alert-info mt-3 py-2 text-center small fw-bold">{status}</div>}
                  </div>
                </div>

                {/* --- CỘT PHẢI: MÀN HÌNH CHÍNH --- */}
                <div className="col-lg-8">
                  <div className="card shadow border-0 rounded-3 h-100 bg-white overflow-hidden">
                    <div className="card-header bg-light py-3">
                      <h5 className="fw-bold mb-0 text-primary">📺 GIÁM SÁT TRỰC TIẾP</h5>
                    </div>
                    <div className="card-body d-flex justify-content-center align-items-center p-0" style={{ height: '600px', backgroundColor: '#eef2f5' }}>

                      {/* Logic hiển thị video thông minh[cite: 15] */}
                      {resultVideoUrl ? (
                        /* 1. Hiện video đã phân tích từ Server */
                        <video src={resultVideoUrl} controls autoPlay className="w-100 h-100" style={{ objectFit: 'contain' }} />
                      ) : videoFile ? (
                        /* 2. Hiện video xem trước ngay khi vừa chọn file (Preview)[cite: 15] */
                        <video
                          src={URL.createObjectURL(videoFile)}
                          controls
                          className="w-100 h-100 opacity-75"
                          style={{ objectFit: 'contain' }}
                        />
                      ) : (
                        /* 3. Hiện placeholder khi chưa chọn gì */
                        <div className="text-center text-muted p-5">
                          <div className="display-1 mb-3">📹</div>
                          <h4 className="fw-bold text-secondary">CHƯA CÓ DỮ LIỆU ĐẦU VÀO</h4>
                          <p>Vui lòng tải lên video giao thông để bắt đầu giám sát.</p>
                        </div>
                      )}

                    </div>
                  </div>
                </div>
              </div>
            } />

            <Route path="/history" element={
              <div className="row g-4">
                <div className="col-12 d-flex justify-content-between align-items-center p-4 rounded-3 shadow bg-white">
                  <h4 className="fw-bold text-danger mb-0">🛡️ KHO DỮ LIỆU PHẠT NGUỘI</h4>
                  <button className="btn btn-danger fw-bold" onClick={handleClearData}>🗑️ XÓA TOÀN BỘ DỮ LIỆU</button>
                </div>
                <div className="col-lg-4">
                  <div className="card shadow border-0 rounded-3 overflow-hidden bg-white">
                    <div className="card-header bg-primary text-white fw-bold">📑 Phiên Phân Tích</div>
                    <div className="table-responsive" style={{ maxHeight: '600px' }}>
                      <table className="table table-hover mb-0">
                        <thead className="table-light"><tr><th>Thời gian</th><th>Video</th><th>Ngưỡng</th></tr></thead>
                        <tbody>
                          {history.map((h, i) => (
                            <tr
                              key={i}
                              onClick={() => setSelectedAnalysisId(selectedAnalysisId === h.id ? null : h.id)}
                              style={{ cursor: 'pointer' }}
                              className={selectedAnalysisId === h.id ? 'table-primary' : ''}
                            >
                              <td>{h.timestamp}</td>
                              <td className="small">{h.filename}</td>
                              <td className="text-danger">{h.speed_limit}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
                <div className="col-lg-8">
                  <div className="card shadow border-0 rounded-3 p-4 bg-white">
                    <h5 className="fw-bold mb-4">
                      📸 Bằng Chứng Vi Phạm ({violations.filter(v => selectedAnalysisId === null || v.analysis_id === selectedAnalysisId).length})
                      {selectedAnalysisId && <button className="btn btn-sm btn-outline-secondary ms-3" onClick={() => setSelectedAnalysisId(null)}>Hiển thị tất cả</button>}
                    </h5>
                    <div className="row row-cols-2 row-cols-md-4 g-4">
                      {violations.filter(v => selectedAnalysisId === null || v.analysis_id === selectedAnalysisId).map((v, i) => (
                        <div className="col" key={i} onClick={() => setSelectedImg(v)} style={{ cursor: 'pointer' }}>
                          <div className="card h-100 border-0 shadow-sm overflow-hidden">
                            <div className="position-relative">
                              <img
                                src={`data:image/jpeg;base64,${v.image_xe_url}`}
                                className="card-img-top"
                                alt="Vehicle"
                                style={{ height: '200px', objectFit: 'cover' }}
                              />
                              <span className="position-absolute bottom-0 start-0 w-100 bg-danger text-white text-center fw-bold py-1 small">{v.speed} km/h</span>
                            </div>
                            <div className="card-body p-2 text-center">
                              <div className="badge bg-dark text-white w-100 py-2 mb-1">{v.vehicle_type}</div>
                              <small className="text-muted d-block fw-bold">ID: {v.id}</small>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            } />
          </Routes>
        </div>

        {/* --- MODAL CHI TIẾT --- */}
        {selectedImg && (
          <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 1050 }} onClick={() => setSelectedImg(null)}>
            <div className="modal-dialog modal-dialog-centered modal-lg" onClick={e => e.stopPropagation()}>
              <div className="modal-content border-0 rounded-4 shadow-lg overflow-hidden">
                <div className="modal-header bg-danger text-white border-0 py-3">
                  <h5 className="modal-title fw-bold">🚨 HỒ SƠ VI PHẠM - ID: {selectedImg.id}</h5>
                  <button className="btn-close btn-close-white" onClick={() => setSelectedImg(null)}></button>
                </div>
                <div className="modal-body bg-light p-4 text-center">
                  <div className="row mb-4">
                    <div className="col-6 border-end"><p className="fw-bold text-secondary mb-1 small">PHƯƠNG TIỆN</p><h3 className="fw-bold">{selectedImg.vehicle_type}</h3></div>
                    <div className="col-6"><p className="fw-bold text-secondary mb-1 small">TỐC ĐỘ</p><h3 className="text-danger fw-bold">{selectedImg.speed} km/h</h3></div>
                  </div>
                  <div className="row g-3">
                    <div className="col-md-6"><div className="card p-1"><img src={`data:image/jpeg;base64,${selectedImg.image_xe_url}`} className="img-fluid rounded" /></div></div>
                    <div className="col-md-6">
                      <div className="card p-1">
                        {selectedImg.image_bienso_url ? <img src={`data:image/jpeg;base64,${selectedImg.image_bienso_url}`} className="img-fluid rounded" /> : <div className="p-5 text-muted">Không có ảnh biển</div>}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <button className="btn btn-primary fw-bold px-5 rounded-pill shadow-sm" onClick={handleDownloadBoth}>
                      ⬇️ TẢI XUỐNG CẢ 2 ẢNH
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;
import sys
import os
import subprocess
import glob
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QFileDialog, 
                             QDoubleSpinBox, QProgressBar, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal

class VideoCutterThread(QThread):
    progress_update = pyqtSignal(int)
    finished_success = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_path, output_dir, interval_seconds):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.interval_seconds = interval_seconds
        self.is_running = True

    def run(self):
        try:
            # Lấy đuôi file gốc (ví dụ: .mp4, .mkv)
            file_ext = os.path.splitext(self.video_path)[1]
            
            # Cú pháp tên file đầu ra cho FFmpeg (VD: video_part_001.mp4)
            output_pattern = os.path.join(self.output_dir, f"video_part_%03d{file_ext}")

            # Đặt % lên 10 để báo GUI biết phần mềm đang bắt đầu xử lý
            self.progress_update.emit(10)

            # Lệnh FFmpeg tự động chia nhỏ video nguyên bản
            cmd = [
                "ffmpeg", 
                "-y", 
                "-i", self.video_path, 
                "-c", "copy", 
                "-f", "segment", 
                "-segment_time", str(self.interval_seconds), 
                "-reset_timestamps", "1",
                output_pattern
            ]
            
            # Chạy lệnh FFmpeg (ẩn cửa sổ console đen)
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Đợi FFmpeg xử lý và cho phép dừng (Stop) nếu người dùng tắt app
            while process.poll() is None:
                if not self.is_running:
                    process.terminate()
                    break
                self.msleep(100) 

            # Xử lý xong, kéo thanh tiến trình lên 100%
            self.progress_update.emit(100)
            
            if self.is_running:
                # Đếm số lượng file vừa được tạo ra trong thư mục
                saved_files = glob.glob(os.path.join(self.output_dir, f"video_part_*{file_ext}"))
                self.finished_success.emit(len(saved_files))
                
        except FileNotFoundError:
            self.error_occurred.emit("Không tìm thấy FFmpeg! Vui lòng cài đặt FFmpeg và thêm vào System PATH.")
        except Exception as e:
            self.error_occurred.emit(f"Lỗi trong quá trình xử lý: {str(e)}")

    def stop(self):
        self.is_running = False


class VideoCutterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cắt Video Hàng Loạt (Siêu Nhanh - Giữ nguyên dung lượng)')
        self.resize(500, 250)
        
        layout = QVBoxLayout()

        # --- Chọn Video ---
        video_layout = QHBoxLayout()
        self.lbl_video = QLabel("Video gốc:")
        self.txt_video = QLineEdit()
        self.txt_video.setReadOnly(True)
        self.btn_video = QPushButton("Chọn File")
        self.btn_video.clicked.connect(self.select_video)
        
        video_layout.addWidget(self.lbl_video)
        video_layout.addWidget(self.txt_video)
        video_layout.addWidget(self.btn_video)
        layout.addLayout(video_layout)

        # --- Chọn Folder Output ---
        folder_layout = QHBoxLayout()
        self.lbl_folder = QLabel("Thư mục lưu:")
        self.txt_folder = QLineEdit()
        self.txt_folder.setReadOnly(True)
        self.btn_folder = QPushButton("Chọn Thư mục")
        self.btn_folder.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.lbl_folder)
        folder_layout.addWidget(self.txt_folder)
        folder_layout.addWidget(self.btn_folder)
        layout.addLayout(folder_layout)

        # --- Khoảng thời gian ---
        interval_layout = QHBoxLayout()
        self.lbl_interval = QLabel("Thời lượng mỗi đoạn (giây):")
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(1.0, 7200.0) # Từ 1 giây đến 2 giờ
        self.spin_interval.setValue(15.0) # Mặc định 15s
        self.spin_interval.setSingleStep(5.0)
        
        interval_layout.addWidget(self.lbl_interval)
        interval_layout.addWidget(self.spin_interval)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)

        # --- Tiến trình ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Nút Bắt đầu ---
        self.btn_start = QPushButton("Bắt Đầu Cắt Video")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.clicked.connect(self.start_cutting)
        layout.addWidget(self.btn_start)

        self.setLayout(layout)

    def select_video(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_name:
            self.txt_video.setText(file_name)

    def select_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Chọn Thư mục lưu video")
        if folder_name:
            self.txt_folder.setText(folder_name)

    def start_cutting(self):
        video_path = self.txt_video.text()
        output_dir = self.txt_folder.text()
        interval = self.spin_interval.value()

        if not video_path or not output_dir:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn video và thư mục lưu!")
            return

        self.btn_start.setEnabled(False)
        self.btn_video.setEnabled(False)
        self.btn_folder.setEnabled(False)
        self.progress_bar.setValue(0)

        self.thread = VideoCutterThread(video_path, output_dir, interval)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.finished_success.connect(self.cutting_finished)
        self.thread.error_occurred.connect(self.cutting_error)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def cutting_finished(self, count):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Hoàn thành", f"Đã cắt thành công {count} đoạn video!")
        self.reset_ui()

    def cutting_error(self, message):
        QMessageBox.critical(self, "Lỗi", message)
        self.reset_ui()

    def reset_ui(self):
        self.btn_start.setEnabled(True)
        self.btn_video.setEnabled(True)
        self.btn_folder.setEnabled(True)

    def closeEvent(self, event):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    ex = VideoCutterApp()
    ex.show()
    sys.exit(app.exec_())
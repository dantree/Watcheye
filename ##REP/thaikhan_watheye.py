import sys
import os
import base64
import hmac
import hashlib
import uuid
import requests
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from ultralytics import YOLO
import cv2
import winsound
import time
import socket

class SolapiMessageSender:
    def __init__(self, api_key, api_secret, from_number):
        self.api_key = api_key
        self.api_secret = api_secret
        self.from_number = from_number
        self.API_URL = 'https://api.solapi.com/messages/v4/send-many/detail'
        
    def _generate_signature(self, date, salt):
        message = f"{date}{salt}"
        signature = hmac.new(
            self.api_secret.encode(), 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
        return signature
        
    def send_message_with_image(self, to, text, image_path):
        try:
            with open(image_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            salt = str(uuid.uuid4())
            signature = self._generate_signature(timestamp, salt)
            
            headers = {
                'Authorization': f'HMAC-SHA256 apiKey={self.api_key}, date={timestamp}, salt={salt}, signature={signature}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messages": [{
                    "to": to,
                    "from": self.from_number,
                    "text": text,
                    "type": "SMS",
                }]
            }
            
            response = requests.post(self.API_URL, headers=headers, json=data)
            return response.json()
        except Exception as e:
            print(f"SMS 발송 오류: {str(e)}")
            return None

class VideoFeed(QFrame):
    def __init__(self, title, available_cameras):
        super().__init__()
        self.setStyleSheet("background-color: #363636;")
        self.layout = QGridLayout(self)
        
        self.header = QFrame()
        self.header_layout = QHBoxLayout(self.header)
        
        self.title = QLabel(title)
        self.title.setStyleSheet("color: white;")
        
        self.camera_selector = QComboBox()
        self.camera_selector.addItems([f"Camera {i}" for i in available_cameras])
        self.camera_selector.setStyleSheet("color: white; background-color: #2b2b2b;")
        
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.camera_selector)
        self.layout.addWidget(self.header, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMinimumSize(580, 400)
        self.layout.addWidget(self.video_label, 1, 0)
        
        self.controls = QFrame()
        self.controls_layout = QHBoxLayout(self.controls)
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        
        self.controls_layout.addWidget(self.start_button)
        self.controls_layout.addWidget(self.stop_button)
        self.layout.addWidget(self.controls, 2, 0)

        self.detection_controls = QFrame()
        self.detection_layout = QHBoxLayout(self.detection_controls)
        
        self.person_toggle = QPushButton("Person")
        self.person_toggle.setCheckable(True)
        self.person_toggle.setChecked(True)
        self.person_toggle.setStyleSheet("""
            QPushButton:checked { background-color: #4CAF50; }
            QPushButton { color: white; padding: 5px; }
        """)
        
        self.helmet_toggle = QPushButton("Helmet")
        self.helmet_toggle.setCheckable(True)
        self.helmet_toggle.setStyleSheet("""
            QPushButton:checked { background-color: #4CAF50; }
            QPushButton { color: white; padding: 5px; }
        """)
        
        self.detection_layout.addWidget(self.person_toggle)
        self.detection_layout.addWidget(self.helmet_toggle)
        self.layout.addWidget(self.detection_controls, 3, 0)

class ObjectDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("산업 안전 감시 시스템")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #2b2b2b;")

        # 캡쳐 및 로그 디렉토리 설정
        today = datetime.now().strftime('%Y%m%d')
        self.capture_dir = os.path.join("captures", today)
        self.log_dir = "logs"
        os.makedirs(self.capture_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"{today}_log.txt")

        # SMS 설정
        self.sms_sender = SolapiMessageSender(
            "NCSGDOVBZV8VNBVU",
            "KPYQ5OK7UQXELIFTC2PNBMFOWK5VVFIN",
            "01084011896"
        )
        self.last_sms_time = 0
        self.sms_interval = 600  # 10분(초 단위)
        self.violation_threshold = 5  # 알람 발송 기준 위반 횟수
        self.admin_numbers = ["01066611015"]
        
        self.captured_images = []
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        self.ip_address = socket.gethostbyname(socket.gethostname())

        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("background-color: #363636;")
        self.status_bar_layout = QGridLayout(self.status_bar)
        self.status_label = QLabel(f"발생 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}    상태: 96%    위치: {self.ip_address}")
        self.status_label.setStyleSheet("color: white;")
        self.status_bar_layout.addWidget(self.status_label)
        self.layout.addWidget(self.status_bar, 0, 0, 1, 2)

        self.available_cameras = self._get_available_cameras()
        self.feed1 = VideoFeed("Event", self.available_cameras)
        self.feed2 = VideoFeed("Live", self.available_cameras)
        self.layout.addWidget(self.feed1, 1, 0)
        self.layout.addWidget(self.feed2, 1, 1)

        self.capture_frame = QFrame()
        self.capture_layout = QVBoxLayout(self.capture_frame)
        self.capture_title = QLabel("최근 캡쳐")
        self.capture_title.setStyleSheet("color: white;")
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setStyleSheet("background-color: black;")
        self.thumbnail_label.setFixedSize(200, 150)
        self.capture_layout.addWidget(self.capture_title)
        self.capture_layout.addWidget(self.thumbnail_label)
        self.layout.addWidget(self.capture_frame, 2, 0)

        self.log_frame = QFrame()
        self.log_frame.setStyleSheet("background-color: #363636;")
        self.log_layout = QVBoxLayout(self.log_frame)
        self.log_title = QLabel("안전 위반 로그")
        self.log_title.setStyleSheet("color: white;")
        self.log_viewer = QTextEdit()
        self.log_viewer.setStyleSheet("color: white; background-color: #2b2b2b;")
        self.log_viewer.setReadOnly(True)
        self.log_layout.addWidget(self.log_title)
        self.log_layout.addWidget(self.log_viewer)
        self.layout.addWidget(self.log_frame, 2, 1)

        self.model = YOLO('yolov8n.pt')
        
        self.caps = {feed: None for feed in [self.feed1, self.feed2]}
        self.timers = {feed: QTimer() for feed in [self.feed1, self.feed2]}
        
        for feed in [self.feed1, self.feed2]:
            timer = self.timers[feed]
            timer.timeout.connect(lambda current_feed=feed: self.update_frame(current_feed))
            feed.start_button.clicked.connect(
                lambda checked, current_feed=feed: self.start_detection(current_feed))
            feed.stop_button.clicked.connect(
                lambda checked, current_feed=feed: self.stop_detection(current_feed))
            feed.camera_selector.currentIndexChanged.connect(
                lambda idx, current_feed=feed: self.change_camera(current_feed))
        
        self.last_alert_time = 0
        self.alert_interval = 2
        self.violation_count = 0

    def add_log(self, message):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{current_time}] {message}"
        
        # UI에 로그 추가
        self.log_viewer.append(log_message)
        
        # 파일에 로그 저장
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def send_violation_alert(self, image_path):
        current_time = time.time()
        if (current_time - self.last_sms_time >= self.sms_interval and 
            self.violation_count >= self.violation_threshold):
            message = f"안전 위반 감지 - {self.violation_count}회 발생\n위치: {self.ip_address}"
            
            for admin in self.admin_numbers:
                response = self.sms_sender.send_message_with_image(admin, message, image_path)
                if response:
                    self.add_log(f"관리자({admin})에게 알림 발송 완료")
                else:
                    self.add_log(f"관리자({admin}) 알림 발송 실패")
            
            self.last_sms_time = current_time
            self.violation_count = 0  # 카운트 리셋

    def _get_available_cameras(self):
        available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        if not available_cameras:
            available_cameras = [0]
        return available_cameras

    def start_detection(self, feed):
        try:
            camera_idx = self.available_cameras[feed.camera_selector.currentIndex()]
            self.caps[feed] = cv2.VideoCapture(camera_idx)
            if self.caps[feed].isOpened():
                self.timers[feed].start(30)
                feed.start_button.setEnabled(False)
                feed.stop_button.setEnabled(True)
                self.add_log(f"카메라 {camera_idx} 감시 시작")
            else:
                self.add_log(f"카메라 {camera_idx} 연결 실패")
        except Exception as e:
            self.add_log(f"카메라 시작 오류: {str(e)}")

    def stop_detection(self, feed):
        try:
            if self.caps[feed]:
                self.timers[feed].stop()
                self.caps[feed].release()
                self.caps[feed] = None
                feed.start_button.setEnabled(True)
                feed.stop_button.setEnabled(False)
                feed.video_label.clear()
                camera_idx = self.available_cameras[feed.camera_selector.currentIndex()]
                self.add_log(f"카메라 {camera_idx} 감시 중지")
        except Exception as e:
            self.add_log(f"카메라 중지 오류: {str(e)}")

    def change_camera(self, feed):
        if self.caps[feed]:
            self.stop_detection(feed)
            self.start_detection(feed)

    def update_frame(self, feed):
        if not self.caps[feed] or not self.caps[feed].isOpened():
            return

        ret, frame = self.caps[feed].read()
        if not ret:
            return

        try:
            current_time = time.time()
            violation_detected = False
            
            results = self.model(frame)[0]
            
            for box in results.boxes:
                class_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                
                if feed.person_toggle.isChecked() and class_id == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Person {conf:.2f}", (x1, y1-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    if feed.helmet_toggle.isChecked():
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "No Helmet", (x1, y1-30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        violation_detected = True

            if violation_detected and feed.helmet_toggle.isChecked():
                if (current_time - self.last_alert_time) >= self.alert_interval:
                    # 이미지 캡쳐 및 저장
                    capture_time = datetime.now().strftime('%Y%m%d-%H%M%S')
                    image_path = os.path.join(self.capture_dir, f"{capture_time}.jpg")
                    cv2.imwrite(image_path, frame)
                    self.captured_images.append(image_path)
                    
                    # 썸네일 업데이트
                    scaled_frame = cv2.resize(frame, (200, 150))
                    self._update_video_label(scaled_frame, self.thumbnail_label)
                    
                    winsound.Beep(1000, 500)
                    self.last_alert_time = current_time
                    self.violation_count += 1
                    self.add_log(f"헬멧 미착용 감지 (위반 횟수: {self.violation_count})")
                    
                    # SMS 알림 발송
                    self.send_violation_alert(image_path)

            self._update_video_label(frame, feed.video_label)

        except Exception as e:
            self.add_log(f"프레임 처리 오류: {str(e)}")

    def _update_video_label(self, frame, label):
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                label.size(), Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.add_log(f"이미지 변환 오류: {str(e)}")

    def closeEvent(self, event):
        for feed in self.caps:
            if self.caps[feed]:
                self.caps[feed].release()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ObjectDetectionApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
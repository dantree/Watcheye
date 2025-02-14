import cv2
import numpy as np
import os
import time
from ultralytics import YOLO
from ..config import settings
from loguru import logger

class DetectionService:
    def __init__(self):
        self.threshold = settings.DETECTION_THRESHOLD
        self.active = False  # 감지 기능 활성 상태 플래그
        # 최근 캡처 기록을 저장 (각 항목은 (None, None, capture_timestamp))
        self.last_captures = []  
        
        try:
            self.model = YOLO('yolov8n.pt')
            logger.info(f"YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading YOLOv8 model: {e}")
            raise

    def enable_detection(self):
        """AI 감지 기능 활성화"""
        self.active = True
        logger.info("Detection enabled.")

    def disable_detection(self):
        """AI 감지 기능 비활성화"""
        self.active = False
        logger.info("Detection disabled.")

    def detect_person(self, image):
        """사람 감지 함수"""
        results = self.model(image)[0]
        detections = []
        
        for box in results.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            
            # class_id 0은 'person' 클래스
            if class_id == 0 and confidence >= self.threshold:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                detections.append({
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                })
        
        return detections

    def process_frame(self, frame):
        """
        프레임 처리 및 결과 반환
        - 감지 활성화 상태에 따라 AI 처리를 수행하고, 캡처 기능 적용
        """
        if not self.active:
            return frame, 0, 0

        # 사람 감지
        detections = self.detect_person(frame)
        num_persons = len(detections)
        num_helmets = 0  # 향후 헬멧 감지 기능 추가 시 사용
        
        # 감지된 객체에 바운딩 박스 그리기
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            
            # 사람 감지 표시 (녹색)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Person {confidence:.2f}", (x1, y1-10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 헬멧 미착용 표시 (빨간색) - 현재는 모든 사람을 헬멧 미착용으로 가정
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "No Helmet", (x1, y1-30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 감지된 객체가 있으면 캡처
        if detections and self.active:
            self.capture_detected_objects(frame, detections)
        
        return frame, num_persons, num_helmets

    def capture_detected_objects(self, frame, detections):
        """감지된 객체가 있을 때 프레임을 캡처합니다."""
        if not detections:
            return
        
        capture_dir = "capture"
        os.makedirs(capture_dir, exist_ok=True)
        current_time = time.time()
        
        # 최근 10초 이내에 캡처한 기록이 있으면 캡처하지 않음
        if any(current_time - cap[2] < 10 for cap in self.last_captures):
            return
        
        # 전체 프레임을 캡처
        filename = os.path.join(capture_dir, f"capture_{int(current_time)}.jpg")
        cv2.imwrite(filename, frame)
        logger.info(f"Captured frame saved: {filename}")
        
        # 캡처 기록 업데이트
        self.last_captures.append((None, None, current_time))
        self.last_captures = [cap for cap in self.last_captures if current_time - cap[2] < 10]

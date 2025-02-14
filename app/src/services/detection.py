import cv2
import torch
import numpy as np
import os
import time
import math
from pathlib import Path
from ..config import settings
from loguru import logger

class DetectionService:
    def __init__(self):
        self.threshold = settings.DETECTION_THRESHOLD
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.active = False
        self.last_captures = []
        # Define capture_dir as instance variable
        self.capture_dir = os.path.abspath("capture")

        if not os.path.exists(self.capture_dir):
            os.makedirs(self.capture_dir)
        
        try:
            self.person_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.person_model.to(self.device)
            logger.info(f"Person detection model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Error loading person detection model: {e}")
            raise

    def process_frame(self, frame):
        """
        프레임 처리 및 결과 반환 (감지 활성화 상태에 따라 AI 처리를 수행하고, 캡처 기능 적용)
        - 프레임의 색상을 BGR에서 RGB로 변환 후 사람 감지를 수행합니다.
        - 감지된 객체에 대해 바운딩 박스를 그립니다.
        - 감지 기능이 활성화되어 있다면, 감지된 객체가 있을 경우 전체 프레임을 캡처합니다.
        """
        # Store original BGR frame for capture
        original_frame = frame.copy()
        
        # BGR -> RGB 변환 (for YOLO detection)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 사람이 감지된 결과 얻기
        persons = self.detect_person(rgb_frame)
        
        # 감지된 객체에 바운딩 박스 그리기 (on BGR frame)
        for _, person in persons.iterrows():
            cv2.rectangle(frame,
                        (int(person['xmin']), int(person['ymin'])),
                        (int(person['xmax']), int(person['ymax'])),
                        (0, 255, 0), 2)
        
        # 감지 기능이 활성화되어 있고, 감지된 객체가 있다면 전체 프레임 캡처
        if self.active:
            # Pass original BGR frame to capture function
            self.capture_detected_objects(original_frame, persons)
        
        return frame, len(persons), 0

    def capture_detected_objects(self, frame, detections):
        """
        감지된 객체가 존재하면, 전체 프레임을 'capture' 폴더에 저장합니다.
        중복 캡처를 방지하기 위해 최근 10초 이내에 캡처한 경우는 저장하지 않습니다.
        """
        logger.debug(f"Capture function called. Detections: {len(detections)}")
        
        if detections.empty:
            logger.debug("No detections, skipping capture")
            return
            
        logger.debug(f"Frame shape: {frame.shape}")
        logger.debug(f"Capture directory: {self.capture_dir}")
        
        current_time = time.time()
        
        if any(current_time - cap[2] < 10 for cap in self.last_captures):
            return
        
        # Frame is already in BGR format, no need to convert
        filename = os.path.join(self.capture_dir, f"capture_{int(current_time)}.jpg")
        
        try:
            success = cv2.imwrite(filename, frame)  # Save original BGR frame
            if success:
                logger.info(f"Captured full frame saved: {filename}")
            else:
                logger.error(f"Failed to save image: {filename}")
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            
        self.last_captures.append((None, None, current_time))
        self.last_captures = [cap for cap in self.last_captures if current_time - cap[2] < 10]

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
        results = self.person_model(image)
        persons = results.pandas().xyxy[0]
        # person 클래스(0)에 대한 결과만 필터링
        persons = persons[persons['class'] == 0]
        return persons[persons['confidence'] >= self.threshold]

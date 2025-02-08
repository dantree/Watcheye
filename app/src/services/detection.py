import cv2
import torch
import numpy as np
from pathlib import Path
from ..config import settings
from loguru import logger

class DetectionService:
    def __init__(self):
        self.threshold = settings.DETECTION_THRESHOLD
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # 사람 감지 모델만 로드
        try:
            self.person_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.person_model.to(self.device)
            logger.info(f"Person detection model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Error loading person detection model: {e}")
            raise
    def enable_detection(self):
        """AI 감지 기능을 활성화합니다."""
        self.active = True
        logger.info("Detection enabled.")

    def disable_detection(self):
        """AI 감지 기능을 비활성화합니다."""
        self.active = False
        logger.info("Detection disabled.")

    def detect_person(self, image):
        """사람 감지 함수"""
        results = self.person_model(image)
        persons = results.pandas().xyxy[0]
        # person 클래스(0)에 대한 결과만 필터링
        persons = persons[persons['class'] == 0]
        return persons[persons['confidence'] >= self.threshold]
        
    def process_frame(self, frame):
        """프레임 처리 및 결과 반환"""
        # BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 사람 감지 수행
        persons = self.detect_person(rgb_frame)
        
        # 결과 이미지에 바운딩 박스 그리기
        for _, person in persons.iterrows():
            cv2.rectangle(frame, 
                        (int(person['xmin']), int(person['ymin'])),
                        (int(person['xmax']), int(person['ymax'])),
                        (0, 255, 0), 2)
            
        return frame, len(persons), 0  # 마지막 0은 helmet 감지 수
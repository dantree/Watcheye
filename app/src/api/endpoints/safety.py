from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ...models import schemas, models, database
from ...core import security
import os
import base64
import hmac
import hashlib
import uuid
import requests
from datetime import datetime
import time
import cv2
import numpy as np
from ultralytics import YOLO

router = APIRouter()

# YOLO 모델 로드
MODEL_PATH = "yolov8n.pt"
model = YOLO(MODEL_PATH)

# 파일 저장 경로 설정
CAPTURE_DIR = os.path.join("captures", datetime.now().strftime('%Y%m%d'))
LOG_DIR = "logs"
os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 객체 탐지 설정
CONFIDENCE_THRESHOLD = 0.5
PERSON_CLASS_ID = 0  # YOLOv8의 person 클래스 ID

# 감지 설정 상태 (기본값)
detection_settings = {
    "person_detection": True,  # 사람 감지
    "helmet_detection": True,  # 헬멧 감지
    "confidence_threshold": 0.5  # 신뢰도 임계값
}

def get_sms_settings(db: Session):
    """SMS 발송 관련 설정을 조회합니다."""
    settings = {}
    for key in ["SMS_API_KEY", "SMS_API_SECRET", "SMS_FROM_NUMBER", "SMS_API_URL"]:
        setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
        if not setting:
            raise HTTPException(status_code=500, detail=f"{key} 설정이 필요합니다.")
        settings[key] = setting.value
    return settings

class SolapiMessageSender:
    def __init__(self, api_key, api_secret, from_number, api_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.from_number = from_number
        self.api_url = api_url
        
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
            
            response = requests.post(self.api_url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"SMS 발송 실패: {str(e)}")

@router.post("/safety/log")
async def create_safety_log(
    message: str,
    level: str = "info",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """새로운 안전 관련 로그를 저장합니다."""
    try:
        log_time = datetime.now()
        log_file = os.path.join(LOG_DIR, f"{log_time.strftime('%Y%m%d')}_safety_log.txt")
        
        # 파일에 로그 저장
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{log_time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
        
        # DB에도 저장
        db_log = models.Event(
            timestamp=log_time,
            level=level,
            message=message,
            type="safety_log",
            user_id=current_user.id
        )
        db.add(db_log)
        db.commit()
        
        # 위반 횟수 확인 및 SMS 발송
        if level == "warning":
            violation_count = db.query(models.Event).filter(
                models.Event.type == "safety_log",
                models.Event.level == "warning",
                models.Event.user_id == current_user.id
            ).count()
            
            if violation_count >= 5:
                await send_safety_alert(
                    phone_numbers=[current_user.phone],
                    message=f"안전 위반 사항이 {violation_count}회 누적되었습니다.\n최근 위반: {message}",
                    db=db
                )
        
        return {"success": True, "message": "안전 로그가 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 저장 실패: {str(e)}")

@router.get("/safety/logs")
async def get_safety_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """저장된 안전 관련 로그를 조회합니다."""
    query = db.query(models.Event).filter(models.Event.type == "safety_log")
    
    if start_date:
        query = query.filter(models.Event.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Event.timestamp <= end_date)
    if level:
        query = query.filter(models.Event.level == level)
    
    logs = query.order_by(models.Event.timestamp.desc()).limit(limit).all()
    return logs

@router.post("/safety/capture")
async def save_safety_capture(
    file: UploadFile = File(...),
    description: str = None,
    violation_type: str = None,
    db: Session = Depends(database.get_db)
):
    """안전 위반 캡쳐 이미지를 저장합니다."""
    try:
        # 파일 저장
        timestamp = datetime.now()
        filename = f"safety_{timestamp.strftime('%Y%m%d-%H%M%S')}.jpg"
        file_path = os.path.join(CAPTURE_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # DB에 기록
        db_capture = models.Event(
            timestamp=timestamp,
            type="safety_capture",
            message=description or "안전 위반 캡쳐 이미지",
            file_path=file_path,
            violation_type=violation_type
        )
        db.add(db_capture)
        db.commit()
        
        return {"success": True, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캡쳐 저장 실패: {str(e)}")

@router.get("/safety/captures")
async def get_safety_captures(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    violation_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(database.get_db)
):
    """저장된 안전 위반 캡쳐 이미지 목록을 조회합니다."""
    query = db.query(models.Event).filter(models.Event.type == "safety_capture")
    
    if start_date:
        query = query.filter(models.Event.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Event.timestamp <= end_date)
    if violation_type:
        query = query.filter(models.Event.violation_type == violation_type)
    
    captures = query.order_by(models.Event.timestamp.desc()).limit(limit).all()
    return captures

@router.post("/safety/alert")
async def send_safety_alert(
    phone_numbers: List[str],
    message: str,
    image_path: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """안전 위반 사항 발생 시 SMS 알림을 발송합니다."""
    try:
        settings = get_sms_settings(db)
        sms_sender = SolapiMessageSender(
            settings["SMS_API_KEY"],
            settings["SMS_API_SECRET"],
            settings["SMS_FROM_NUMBER"],
            settings["SMS_API_URL"]
        )
        
        results = []
        for phone in phone_numbers:
            if image_path:
                response = sms_sender.send_message_with_image(phone, message, image_path)
            else:
                response = sms_sender.send_message_with_image(phone, message, None)
            results.append({"phone": phone, "response": response})
        
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 발송 실패: {str(e)}")

@router.get("/safety/violation-count")
async def get_violation_count(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    violation_type: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """특정 기간 동안의 안전 위반 횟수를 조회합니다."""
    query = db.query(models.Event).filter(models.Event.type == "safety_capture")
    
    if start_date:
        query = query.filter(models.Event.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Event.timestamp <= end_date)
    if violation_type:
        query = query.filter(models.Event.violation_type == violation_type)
    
    count = query.count()
    return {"violation_count": count}

@router.get("/safety/detection-settings")
async def get_detection_settings():
    """현재 감지 설정을 조회합니다."""
    return detection_settings

@router.post("/safety/detection-settings")
async def update_detection_settings(
    person_detection: Optional[bool] = None,
    helmet_detection: Optional[bool] = None,
    confidence_threshold: Optional[float] = None
):
    """감지 설정을 업데이트합니다."""
    global detection_settings, CONFIDENCE_THRESHOLD
    
    if person_detection is not None:
        detection_settings["person_detection"] = person_detection
    if helmet_detection is not None:
        detection_settings["helmet_detection"] = helmet_detection
    if confidence_threshold is not None:
        detection_settings["confidence_threshold"] = confidence_threshold
        CONFIDENCE_THRESHOLD = confidence_threshold
    
    return detection_settings

@router.post("/safety/detect-stream")
async def detect_objects_stream(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """실시간 스트림에서 객체를 탐지합니다."""
    try:
        # 이미지 읽기
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 원본 이미지 복사 (나중에 위반 상황 저장용)
        original_image = image.copy()
        
        results = model(image)[0]
        detections = []
        violations = []
        
        for box in results.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            
            if confidence > detection_settings["confidence_threshold"]:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # 사람 감지가 활성화되어 있고, 사람이 탐지된 경우
                if detection_settings["person_detection"] and class_id == PERSON_CLASS_ID:
                    detection = {
                        "class_id": class_id,
                        "class_name": "person",
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2]
                    }
                    detections.append(detection)
                    
                    # 녹색 박스로 사람 표시
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(image, f"Person {confidence:.2f}", (x1, y1-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # 헬멧 감지가 활성화된 경우 위반 체크
                    if detection_settings["helmet_detection"]:
                        # 여기서는 간단히 모든 사람을 헬멧 미착용으로 가정
                        # 실제로는 더 복잡한 헬멧 감지 로직이 필요
                        violation = {
                            "type": "no_helmet",
                            "bbox": [x1, y1, x2, y2],
                            "confidence": confidence
                        }
                        violations.append(violation)
                        
                        # 빨간색 박스로 위반 표시
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(image, "No Helmet", (x1, y1-30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # 위반 사항이 있고 헬멧 감지가 활성화되어 있으면 로그 및 이미지 저장
        if violations and detection_settings["helmet_detection"]:
            timestamp = datetime.now()
            filename = f"violation_{timestamp.strftime('%Y%m%d-%H%M%S')}.jpg"
            file_path = os.path.join(CAPTURE_DIR, filename)
            
            # 원본 이미지에 위반 표시하여 저장
            for violation in violations:
                x1, y1, x2, y2 = violation["bbox"]
                cv2.rectangle(original_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(original_image, "No Helmet", (x1, y1-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            cv2.imwrite(file_path, original_image)
            
            # 로그 저장
            for violation in violations:
                await create_safety_log(
                    message=f"안전모 미착용 감지 (신뢰도: {violation['confidence']:.2f})",
                    level="warning",
                    db=db,
                    current_user=current_user
                )
        
        # 이미지를 base64로 인코딩
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "success": True,
            "image": image_base64,
            "detections": detections,
            "violations": violations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실시간 객체 탐지 실패: {str(e)}") 
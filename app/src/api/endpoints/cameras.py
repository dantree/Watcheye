from fastapi import APIRouter, HTTPException, Response, Body
from fastapi.responses import StreamingResponse
import cv2
from typing import Dict, Any
from ...services.camera_manager import CameraManager
from loguru import logger
import json
import os
from datetime import datetime

router = APIRouter()
camera_manager = CameraManager()

# 설정 파일 경로
CAMERA_SETTINGS_FILE = "data/camera_settings.json"

# 설정 파일이 저장될 디렉토리 생성
os.makedirs(os.path.dirname(CAMERA_SETTINGS_FILE), exist_ok=True)

def load_camera_settings() -> dict:
    """카메라 설정을 로드합니다."""
    try:
        if os.path.exists(CAMERA_SETTINGS_FILE):
            with open(CAMERA_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"카메라 설정 로드 실패: {e}")
    return {
        "camera1": {
            "name": "카메라 1",
            "url": "",
            "resolution": "1280x720",
            "fps": "30"
        },
        "camera2": {
            "name": "카메라 2",
            "url": "",
            "resolution": "1280x720",
            "fps": "30"
        },
        "common": {
            "autoReconnect": True,
            "reconnectInterval": 5,
            "bufferSize": 5,
            "qualityOptimization": True
        },
        "recording": {
            "autoRecord": False,
            "format": "mp4",
            "retention": 30
        }
    }

@router.post("/cameras/{camera_id}")
async def add_camera(camera_id: int, url: str):
    try:
        camera_manager.add_camera(camera_id, url)
        return {"message": f"Camera {camera_id} added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: int):
    try:
        camera_manager.remove_camera(camera_id)
        return {"message": f"Camera {camera_id} removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cameras/")
async def list_cameras():
    return {"cameras": list(camera_manager.cameras.keys())}

# 노트북 웹캠용 간단한 초기화
@router.post("/init-webcam")
async def init_webcam():
    """노트북 웹캠 초기화"""
    try:
        # 웹캠 ID 0으로 초기화 (대부분의 노트북에서 기본 웹캠은 0)
        camera_manager.add_camera(0, 0)  # URL 대신 0을 사용
        return {"message": "Webcam initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/settings/threshold")
async def update_threshold(threshold: float):
    """감지 임계값 업데이트"""
    try:
        camera_manager.detection_service.threshold = threshold
        return {"message": "Threshold updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cameras/settings")
async def get_camera_settings():
    """카메라 설정을 조회합니다."""
    try:
        settings = load_camera_settings()
        return {"success": True, **settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cameras/settings")
async def update_camera_settings(settings: Dict[str, Any]):
    """카메라 설정을 업데이트합니다."""
    try:
        with open(CAMERA_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": "설정이 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cameras/{camera_id}/stream")
async def stream_camera(camera_id: int, ai: bool = False):
    """
    카메라 스트리밍 엔드포인트
      - 쿼리 파라미터 ai가 True이면 DetectionService를 적용하여 AI 감지가 된 프레임을 스트리밍
      - ai가 False이면 원본 스트림을 그대로 스트리밍
    """
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    def generate_frames():
        while True:
            try:
                frame = camera.get_frame()
                if frame is None:
                    continue

                # ai 파라미터가 True이면 detection_service를 적용
                if ai:
                    if camera.detection_service:
                        try:
                            # process_frame은 프레임에 바운딩 박스를 그린 후, (프레임, 감지된 사람 수, helmet 수)를 반환
                            frame, num_persons, num_helmets = camera.detection_service.process_frame(frame)
                        except Exception as e:
                            logger.error(f"Error processing frame with AI: {str(e)}")
                            continue

                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                continue

    return StreamingResponse(
        generate_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )
    
     
@router.post("/cameras/{camera_id}/toggle")
async def toggle_camera(camera_id: int):
    """카메라 ON/OFF 토글 엔드포인트"""
    try:
        status = camera_manager.toggle_camera(camera_id)
        return {"status": status}
    except Exception as e:
        logger.error(f"Camera {camera_id} toggle error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"카메라 제어 중 오류 발생: {str(e)}")

@router.post("/cameras/{camera_id}/ai")
async def toggle_ai(camera_id: int, enabled: bool = Body(..., embed=True)):
    """
    카메라의 AI 감지 기능 토글 엔드포인트

    매개변수:
      - camera_id: 제어할 카메라의 ID
      - enabled: AI 감지 기능 활성 여부 (True: 켜기, False: 끄기)

    반환:
      - success: 요청이 성공적으로 처리되었음을 나타냄 (항상 True)
      - ai_enabled: 실제로 AI 감지 기능이 활성화되었는지 여부
    """
    try:
        if not camera_manager.get_camera(camera_id):
            raise HTTPException(status_code=404, detail="Camera not found")
        
        ai_enabled = camera_manager.toggle_ai(camera_id, enabled)
        return {"success": True, "ai_enabled": ai_enabled}
    except Exception as e:
        logger.error(f"Error toggling AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))
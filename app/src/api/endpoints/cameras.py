from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import cv2
from typing import Dict
from ...services.camera_manager import CameraManager
from loguru import logger

router = APIRouter()
camera_manager = CameraManager()

# 카메라 상태 저장을 위한 변수
webcam_active = False
webcam_cap = None

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

@router.get("/cameras/{camera_id}/stream")
async def stream_camera(camera_id: int):
    """카메라 스트리밍 엔드포인트"""
    # 카메라 1은 웹캠으로 처리
    if camera_id == 1:
        def generate_webcam():
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("카메라 장치를 열 수 없습니다!")
                return
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        logger.error("프레임 캡처에 실패했습니다.")
                        break
                    
                    # AI 모델로 프레임 처리
                    if camera_manager.detection_service:
                        try:
                            frame, num_persons, num_helmets = camera_manager.detection_service.process_frame(frame)
                        except Exception as e:
                            logger.error(f"Error processing frame: {str(e)}")
                    
                    # JPEG으로 인코딩
                    ret_enc, buffer = cv2.imencode('.jpg', frame)
                    if not ret_enc:
                        logger.error("프레임 JPEG 인코딩에 실패했습니다.")
                        continue
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            finally:
                cap.release()
        
        return StreamingResponse(
            generate_webcam(),
            media_type='multipart/x-mixed-replace; boundary=frame'
        )
    
    # 다른 카메라들은 기존 로직으로 처리
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    def generate_frames():
        while True:
            try:
                frame = camera.get_frame()
                if frame is None:
                    continue
                    
                # AI 모델로 프레임 처리
                if camera.detection_service:
                    try:
                        frame, num_persons, num_helmets = camera.detection_service.process_frame(frame)
                    except Exception as e:
                        logger.error(f"Error processing frame: {str(e)}")
                        continue
                    
                # JPEG으로 인코딩
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # multipart/x-mixed-replace 형식으로 스트리밍
                yield (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                continue
    
    return StreamingResponse(
        generate_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

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

@router.post("/cameras/{camera_id}/toggle")
async def toggle_camera(camera_id: int):
    """카메라 ON/OFF 토글"""
    global webcam_active, webcam_cap
    
    if camera_id == 1:  # 웹캠
        if webcam_active:
            if webcam_cap:
                webcam_cap.release()
                webcam_cap = None
            webcam_active = False
            return {"status": "off"}
        else:
            webcam_active = True
            return {"status": "on"}
    else:
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        camera.toggle_active()
        return {"status": "on" if camera.is_active else "off"}

@router.post("/cameras/{camera_id}/ai")
async def toggle_ai(camera_id: int, enabled: bool):
    """카메라의 AI 감지 기능을 켜거나 끕니다."""
    try:
        if camera_id == 1:  # 웹캠
            if enabled:
                camera_manager.detection_service.enable_detection()
            else:
                camera_manager.detection_service.disable_detection()
        else:
            camera = camera_manager.get_camera(camera_id)
            if not camera:
                raise HTTPException(status_code=404, detail="Camera not found")
            
            if enabled:
                camera.enable_detection()
            else:
                camera.disable_detection()
        
        return {"success": True, "ai_enabled": enabled}
    except Exception as e:
        logger.error(f"AI 토글 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
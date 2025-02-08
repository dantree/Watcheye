from typing import Dict
from .camera import CameraService
from .detection import DetectionService
from loguru import logger

class CameraManager:
    def __init__(self):
        self.cameras: Dict[int, CameraService] = {}
        self.detection_service = DetectionService()
        
    def add_camera(self, camera_id: int, url: str):
        """카메라 추가"""
        if camera_id in self.cameras:
            logger.warning(f"Camera {camera_id} already exists")
            return
            
        camera = CameraService(camera_id, url)
        camera.detection_service = self.detection_service
        # 초기 상태: 카메라는 off, AI는 off
        camera.active = False
        camera.activeAI = False
        self.cameras[camera_id] = camera
        # 추가 후 카메라를 시작(원하는 경우)
        camera.start()
        camera.active = True
        logger.info(f"Added camera {camera_id}")
        
    def remove_camera(self, camera_id: int):
        """카메라 제거"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            logger.info(f"Removed camera {camera_id}")
            
    def get_camera(self, camera_id: int) -> CameraService:
        """카메라 인스턴스 반환"""
        return self.cameras.get(camera_id)
    
    def toggle_camera(self, camera_id: int) -> str:
        """
        카메라 on/off 토글
        :return: 현재 상태("on" 또는 "off")
        """
        camera = self.get_camera(camera_id)
        if not camera:
            raise Exception("Camera not found")
        if camera.active:
            camera.stop()
            camera.active = False
            logger.info(f"Camera {camera_id} turned off")
            return "off"
        else:
            camera.start()
            camera.active = True
            logger.info(f"Camera {camera_id} turned on")
            return "on"
    
    def toggle_ai(self, camera_id: int, enabled: bool) -> bool:
        """
        카메라의 AI 감지 기능 토글
        :param enabled: True이면 AI 감지를 활성화, False이면 비활성화
        :return: 현재 AI 활성 상태 (True 또는 False)
        """
        camera = self.get_camera(camera_id)
        if not camera:
            raise Exception("Camera not found")
        # 여기서는 각 카메라 인스턴스에 activeAI 속성을 업데이트합니다.
        camera.activeAI = enabled
        logger.info(f"Camera {camera_id} AI toggled to {enabled}")
        return enabled

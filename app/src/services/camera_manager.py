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
        self.cameras[camera_id] = camera
        camera.start()
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
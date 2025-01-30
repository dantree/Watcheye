import cv2
import threading
from queue import Queue
from loguru import logger
from ..config import settings

class CameraService:
    def __init__(self, camera_id: int, url: str):
        self.camera_id = camera_id
        self.url = url
        self.is_running = False
        self.frame_queue = Queue(maxsize=10)
        self.detection_service = None  # DetectionService 인스턴스 저장용
        
    def start(self):
        """카메라 스트리밍 시작"""
        try:
            # 웹캠 연결 테스트
            cap = cv2.VideoCapture(self.url)
            if not cap.isOpened():
                raise Exception(f"Failed to open camera {self.camera_id}")
            cap.release()
            
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True  # 메인 스레드 종료시 같이 종료
            self.capture_thread.start()
            logger.info(f"Camera {self.camera_id} started streaming")
        except Exception as e:
            logger.error(f"Failed to start camera {self.camera_id}: {str(e)}")
            raise
        
    def stop(self):
        """카메라 스트리밍 중지"""
        self.is_running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1.0)
        logger.info(f"Camera {self.camera_id} stopped streaming")
        
    def _capture_frames(self):
        """프레임 캡처 스레드"""
        cap = cv2.VideoCapture(self.url)
        
        try:
            while self.is_running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.error(f"Failed to read frame from camera {self.camera_id}")
                    break
                    
                # 이전 프레임이 처리되지 않았다면 스킵
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                    
                self.frame_queue.put(frame)
                
        except Exception as e:
            logger.error(f"Error in capture thread for camera {self.camera_id}: {str(e)}")
        finally:
            cap.release()
        
    def get_frame(self):
        """최신 프레임 반환"""
        try:
            if self.frame_queue.empty():
                return None
            return self.frame_queue.get_nowait()
        except:
            return None 
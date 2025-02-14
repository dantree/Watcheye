from fastapi import APIRouter, HTTPException
import psutil
import GPUtil
from datetime import datetime
from typing import List, Dict, Any
import logging
import os
import json
from pydantic import BaseModel
from ...models.settings import load_settings, save_settings

router = APIRouter(prefix="/api/v1", tags=["system"])

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정 파일 경로
SETTINGS_FILE = "data/settings.json"

# 설정 모델
class SystemSettings(BaseModel):
    sms_phone: str = ""
    violation_threshold: int = 5
    auto_logout_time: int = 30
    notification_sound: bool = True
    ai_sensitivity: str = "medium"
    auto_ai_enable: bool = False
    sms_notification: bool = False
    email_notification: bool = False
    person_detection: bool = True
    helmet_detection: bool = True
    ppe_detection: bool = False
    danger_zone_detection: bool = False

# 설정 파일이 저장될 디렉토리 생성
os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

def load_settings() -> SystemSettings:
    """설정 파일을 로드합니다."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return SystemSettings(**json.load(f))
    except Exception as e:
        logger.error(f"설정 로드 실패: {e}")
    return SystemSettings()

def save_settings(settings: Dict[str, Any]) -> bool:
    """설정을 파일에 저장합니다."""
    try:
        # 기존 설정 로드
        current_settings = load_settings().dict()
        # 새로운 설정으로 업데이트
        current_settings.update(settings)
        
        # 설정 저장
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"설정 저장 실패: {e}")
        return False

@router.get("/system/status")
async def get_system_status():
    """시스템 상태 정보를 반환합니다."""
    try:
        monitor = SystemMonitor()
        
        status = {
            "success": True,
            "cpu": monitor.get_cpu_info(),
            "memory": monitor.get_memory_info(),
            "disk": monitor.get_disk_info(),
            "gpu": monitor.get_gpu_info(),
            "logs": monitor.get_system_logs()
        }
        
        return status
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/system/settings")
async def get_settings():
    """시스템 설정을 반환합니다."""
    try:
        settings = load_settings()
        return {"success": True, "settings": settings.dict()}
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}")
        return {"success": False, "error": str(e)}

@router.post("/system/settings")
async def update_settings(settings: Dict[str, Any]):
    """시스템 설정을 업데이트합니다."""
    try:
        if save_settings(settings):
            return {"success": True, "message": "설정이 저장되었습니다."}
        return {"success": False, "error": "설정 저장에 실패했습니다."}
    except Exception as e:
        logger.error(f"설정 업데이트 실패: {e}")
        return {"success": False, "error": str(e)}

class SystemMonitor:
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        process_count = len(psutil.pids())
        
        return {
            "usage": cpu_percent,
            "cores": cpu_count,
            "processes": process_count
        }
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "used": memory.used,
            "free": memory.available
        }
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free
        }
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 첫 번째 GPU 정보
                return {
                    "usage": gpu.load * 100,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "temperature": gpu.temperature
                }
        except Exception as e:
            logger.warning(f"GPU 정보 조회 실패: {e}")
        
        # GPU 정보를 가져올 수 없는 경우 기본값 반환
        return {
            "usage": 0,
            "memory_total": 0,
            "memory_used": 0,
            "temperature": 0
        }

    @staticmethod
    def get_system_logs() -> List[Dict[str, Any]]:
        # 시스템 로그를 가져오는 로직
        # 예시로 최근 로그 몇 개를 반환
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": "시스템이 정상 작동 중입니다."
            }
        ]

# 시스템 로그 저장을 위한 간단한 인메모리 큐
system_logs = []
MAX_LOGS = 1000

def add_system_log(level: str, message: str):
    """시스템 로그를 추가합니다."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message
    }
    
    system_logs.append(log_entry)
    if len(system_logs) > MAX_LOGS:
        system_logs.pop(0)  # 가장 오래된 로그 제거
    
    return log_entry

@router.post("/log")
async def add_log(level: str, message: str):
    """새로운 시스템 로그를 추가합니다."""
    try:
        log_entry = add_system_log(level, message)
        return {"success": True, "log": log_entry}
    except Exception as e:
        logger.error(f"로그 추가 실패: {e}")
        return {"success": False, "error": str(e)} 
    
@router.get("/system/logs")
async def get_system_logs():
    """
    최근 시스템 로그(예: 마지막 50줄)를 반환합니다.
    (이 예시는 로그가 'logs/system.log' 파일에 기록된다고 가정합니다.)
    """
    log_file = "logs/system.log"
    if not os.path.exists(log_file):
        return {"logs": []}
    with open(log_file, "r") as f:
        lines = f.readlines()[-100:]  # 최근 50줄만 읽음
    # 각 로그 항목을 JSON 객체로 변환 (원하는 형식으로 수정 가능)
    logs = []
    for line in lines:
        # 여기서는 단순히 문자열만 반환합니다.
        logs.append({"timestamp": "", "level": "", "message": line.strip()})
    return {"logs": logs}

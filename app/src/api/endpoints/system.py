from fastapi import APIRouter
import psutil
import GPUtil
from datetime import datetime
from typing import List, Dict, Any
import logging

router = APIRouter()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@router.get("/status")
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
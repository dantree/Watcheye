from pydantic import BaseModel
import json
import os
from typing import Optional

class SystemSettings(BaseModel):
    sms_phone: Optional[str] = None
    violation_threshold: Optional[int] = 3
    auto_logout_time: Optional[int] = 30
    notification_sound: Optional[bool] = True
    ai_sensitivity: Optional[str] = "medium"
    auto_ai_enable: Optional[bool] = False
    sms_notification: Optional[bool] = False
    email_notification: Optional[bool] = False
    person_detection: Optional[bool] = True
    helmet_detection: Optional[bool] = True
    ppe_detection: Optional[bool] = False
    danger_zone_detection: Optional[bool] = False

def get_settings_file_path():
    """설정 파일의 경로를 반환합니다."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, "settings.json")

def load_settings() -> SystemSettings:
    """설정 파일에서 설정을 로드합니다."""
    settings_path = get_settings_file_path()
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings_dict = json.load(f)
                return SystemSettings(**settings_dict)
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {e}")
    return SystemSettings()

def save_settings(settings_dict: dict) -> bool:
    """설정을 파일에 저장합니다."""
    try:
        settings = SystemSettings(**settings_dict)
        settings_path = get_settings_file_path()
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings.dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 저장 중 오류 발생: {e}")
        return False 
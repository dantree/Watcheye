from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...models import schemas, models, database
from ...core import security

router = APIRouter(tags=["settings"])

@router.get("/settings/", response_model=List[schemas.SystemSetting])
async def get_settings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """시스템 설정 목록을 조회합니다."""
    try:
        settings = db.query(models.SystemSetting).all()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/{key}", response_model=schemas.SystemSetting)
async def get_setting(
    key: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """특정 설정을 조회합니다."""
    try:
        setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
        if not setting:
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
        return setting
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings", response_model=schemas.SystemSetting)
async def create_or_update_settings(
    settings: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """설정을 생성하거나 업데이트합니다."""
    try:
        # 각 설정 항목을 순회하며 업데이트 또는 생성
        for key, value in settings.items():
            db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
            if db_setting:
                # 기존 설정 업데이트
                db_setting.value = str(value)
            else:
                # 새 설정 생성
                db_setting = models.SystemSetting(key=key, value=str(value))
                db.add(db_setting)
        
        db.commit()
        return {"success": True, "message": "설정이 저장되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/position")
async def update_position(
    position: dict,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """사용자의 직책을 업데이트합니다."""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="인증이 필요합니다.")
        current_user.position = position.get("position", "")
        db.commit()
        return {"success": True, "message": "직책이 업데이트되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 
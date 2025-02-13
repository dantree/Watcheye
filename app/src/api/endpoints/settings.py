from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...models import schemas, models, database
from ...core import security

router = APIRouter()

@router.get("/settings/", response_model=List[schemas.SystemSetting])
async def get_settings(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """시스템 설정 목록을 조회합니다."""
    settings = db.query(models.SystemSetting).all()
    return settings

@router.get("/settings/{key}", response_model=schemas.SystemSetting)
async def get_setting(
    key: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """특정 설정을 조회합니다."""
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    return setting

@router.post("/settings/", response_model=schemas.SystemSetting)
async def create_setting(
    setting: schemas.SystemSettingCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """새로운 설정을 추가합니다."""
    db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == setting.key).first()
    if db_setting:
        raise HTTPException(status_code=400, detail="이미 존재하는 설정입니다.")
    
    db_setting = models.SystemSetting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.put("/settings/{key}", response_model=schemas.SystemSetting)
async def update_setting(
    key: str,
    setting: schemas.SystemSettingCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """설정을 수정합니다."""
    db_setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")
    
    for field, value in setting.dict(exclude_unset=True).items():
        setattr(db_setting, field, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting 
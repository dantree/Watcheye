from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ...api.endpoints.auth import get_current_user
from ...models.database import get_db
import os
from pathlib import Path

# 현재 파일의 디렉토리를 기준으로 템플릿 디렉토리 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="", tags=["views"])

@router.get("/", response_class=HTMLResponse)
async def view_page(request: Request, db: Session = Depends(get_db)):
    # Check if access_token cookie exists
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login", status_code=302)
    try:
        # Directly call get_current_user with request, no manual token extraction needed
        current_user = await get_current_user(request, db=db)
        
        # 임시로 카메라 데이터 생성 (실제로는 DB에서 가져와야 함)
        cameras = [
            {"id": 1, "name": "카메라 1"},
            {"id": 2, "name": "카메라 2"},
            {"id": 3, "name": "카메라 3"},
            {"id": 4, "name": "카메라 4"}
        ]
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user": current_user,
                "cameras": cameras
            }
        )
    except Exception as e:
        print("View page error:", e)
        return RedirectResponse(url="/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token", path="/")
    return response
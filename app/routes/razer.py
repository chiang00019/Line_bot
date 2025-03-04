from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.razer_service import RazerService
from app.database import get_db

router = APIRouter()

@router.post("/razer/deposit")
async def deposit(user_id: str, user_name: str, password: str, razer_email: str, razer_password: str, deposit_count: int, db: Session = Depends(get_db)):
    """
    接收 Razer 儲值請求，使用 Playwright 模擬網頁操作
    - user_id: 儲值帳戶 ID
    - user_name: 儲值帳戶名稱
    - password: 儲值帳戶密碼
    - razer_email: Razer 登入信箱
    - razer_password: Razer 登入密碼
    - deposit_count: 儲值次數
    """
    razer_service = RazerService(db)
    result = razer_service.perform_deposit(user_id, user_name, password, razer_email, razer_password, deposit_count)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "message": result["message"],
        "first_image": result["first_image"],
        "zip_file": "儲值紀錄.zip"
    }

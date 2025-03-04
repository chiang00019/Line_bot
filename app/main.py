from fastapi import FastAPI
from app.routes import linebot, token, email, razer, admin

app = FastAPI(title="Razer 自動儲值系統")

# 註冊 API 路由
app.include_router(linebot.router, prefix="/linebot", tags=["Line Bot"])
app.include_router(token.router, prefix="/token", tags=["Token 管理"])
app.include_router(email.router, prefix="/email", tags=["Email 對帳"])
app.include_router(razer.router, prefix="/razer", tags=["Razer 儲值"])
app.include_router(admin.router, prefix="/admin", tags=["群組管理"])

@app.get("/")
async def root():
    return {"message": "Razer Auto-Topup System is running 🚀"}

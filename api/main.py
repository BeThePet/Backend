from fastapi import FastAPI
from sqlalchemy import text

from api.db.session import SessionLocal
from api.routers import user

app = FastAPI()

# 라우터 등록
app.include_router(user.router, prefix="/users", tags=["User"])


@app.get("/")
def read_root():
    try:
        db = SessionLocal()
        # 연결 테스트용 쿼리 — PostgreSQL 기준
        db.execute(text("SELECT 1"))
        return {"message": "RDS 연결 성공"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

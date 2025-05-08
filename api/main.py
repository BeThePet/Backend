from db.base import Base
from fastapi import FastAPI

from api.db.session import engine
from api.routers import user

app = FastAPI()


# DB 테이블 자동 생성
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# 라우터 등록
app.include_router(user.router, prefix="/users", tags=["User"])

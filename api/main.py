from db.base import Base
from fastapi import FastAPI

from api.db.session import engine
from api.routers import dog, health, mbti, medic, option, user

app = FastAPI()


# DB 테이블 자동 생성
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(dog.router, prefix="/dog", tags=["Dog"])
app.include_router(option.router, prefix="/option", tags=["Option"])
app.include_router(mbti.router, prefix="/mbti", tags=["Mbti"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(medic.router, prefix="/medications", tags=["Medications"])

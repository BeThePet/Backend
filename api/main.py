from db.base import Base
from fastapi import FastAPI

from api.db.session import engine
from api.routers import dog, mbti, option, user

app = FastAPI()


# DB 테이블 자동 생성
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(user.router, prefix="/users", tags=["User"])
app.include_router(dog.router, prefix="/dog", tags=["Dog"])
app.include_router(option.router, prefix="/option", tags=["Option"])
app.include_router(mbti.router, prefix="/mbti", tags=["Mbti"])

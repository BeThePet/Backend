from db.base import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from api.core.config import settings
from api.db.session import engine
from api.routers import dog, emergency, health, mbti, medic, option, user, vaccine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",  
    redoc_url="/redoc",  
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 설정
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


# 보안 헤더 미들웨어
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# DB 테이블 자동 생성
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(dog.router, prefix="/dog", tags=["Dog"])
app.include_router(option.router, prefix="/option", tags=["Option"])
app.include_router(mbti.router, prefix="/mbti", tags=["Mbti"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(medic.router, prefix="/medication", tags=["Medication"])
app.include_router(vaccine.router, prefix="/vaccine", tags=["Vaccine"])
app.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])

import os
from typing import List

from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "BethePet API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "반려견 헬스케어 플랫폼 API"

    # 데이터베이스 설정
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 보안 설정
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React 개발 서버 (직접 접근)
        "http://localhost",  # Nginx 프록시를 통한 접근
        "http://localhost:80",  # 명시적 포트
        "https://yoon.today",  # 프로덕션 프론트엔드
        "https://api.yoon.today",  # 프로덕션 백엔드
    ]

    # 호스트 설정
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "api.yoon.today"]

    # 환경 설정
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    #ENVIRONMENT: str = "development"  # 프로덕션 환경

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_REGION: str = "ap-northeast-2"

    class Config:
        case_sensitive = True
        env_file = ".env"

        # 환경 변수 우선순위:
        # 1. 시스템 환경 변수
        # 2. .env 파일
        # 3. 기본값


# 설정 인스턴스 생성
settings = Settings()

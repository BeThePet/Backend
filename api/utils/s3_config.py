from dataclasses import dataclass

from api.core.config import settings


@dataclass
class S3Config:
    access_key: str
    secret_key: str
    bucket_name: str
    region: str = "ap-northeast-2"


def get_s3_config() -> S3Config:
    """설정에서 S3 설정을 로드"""
    if not all(
        [
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            settings.AWS_S3_BUCKET_NAME,
        ]
    ):
        raise ValueError("AWS S3 설정이 누락되었습니다. 환경변수를 확인하세요.")

    return S3Config(
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        bucket_name=settings.AWS_S3_BUCKET_NAME,
        region=settings.AWS_S3_REGION,
    )

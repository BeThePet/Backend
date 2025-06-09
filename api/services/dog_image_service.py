import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from db.models import Dog
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.utils.s3_config import get_s3_config


class DogImageService:
    @staticmethod
    async def upload_image(user_id: int, file: UploadFile, db: Session) -> str:
        """반려견 프로필 이미지 첫 업로드"""
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        if dog.profile_image_url:
            raise HTTPException(
                status_code=400,
                detail="이미 프로필 이미지가 존재합니다. PUT을 사용하세요.",
            )

        # S3에 이미지 업로드
        image_url = await DogImageService._upload_to_s3(file, user_id, dog.id)

        # DB 업데이트
        dog.profile_image_url = image_url
        db.commit()
        db.refresh(dog)

        return image_url

    @staticmethod
    async def update_image(user_id: int, file: UploadFile, db: Session) -> str:
        """반려견 프로필 이미지 교체"""
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        # S3에 새 이미지 업로드
        image_url = await DogImageService._upload_to_s3(file, user_id, dog.id)

        # DB 업데이트 (기존 URL은 자동으로 덮어씀)
        dog.profile_image_url = image_url
        db.commit()
        db.refresh(dog)

        return image_url

    @staticmethod
    def get_image_url(user_id: int, db: Session) -> Optional[str]:
        """반려견 프로필 이미지 URL 조회"""
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        return dog.profile_image_url

    @staticmethod
    def delete_image(user_id: int, db: Session):
        """반려견 프로필 이미지 삭제 (기본 이미지로 변경)"""
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        # DB에서 URL 제거 (S3 파일은 삭제하지 않음)
        dog.profile_image_url = None
        db.commit()

    @staticmethod
    async def _upload_to_s3(file: UploadFile, user_id: int, dog_id: int) -> str:
        """S3에 이미지 업로드"""
        try:
            s3_config = get_s3_config()
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=s3_config.access_key,
                aws_secret_access_key=s3_config.secret_key,
                region_name=s3_config.region,
            )

            # 파일명 생성: dogs/{user_id}/{dog_id}/profile_{uuid}.{ext}
            file_extension = (
                file.filename.split(".")[-1] if "." in file.filename else "jpg"
            )
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            s3_key = f"dogs/{user_id}/{dog_id}/profile_{unique_filename}"

            # S3 업로드
            file_content = await file.read()
            s3_client.put_object(
                Bucket=s3_config.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type,
            )

            # URL 생성
            image_url = f"https://{s3_config.bucket_name}.s3.{s3_config.region}.amazonaws.com/{s3_key}"
            return image_url

        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"이미지 업로드 중 오류 발생: {str(e)}"
            )

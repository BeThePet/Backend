from core.security import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.schemas.dog import DogImageResponse
from api.services.dog_image_service import DogImageService

router = APIRouter()


@router.post("/", response_model=DogImageResponse)
async def upload_dog_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """반려견 프로필 이미지 첫 업로드"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_url = await DogImageService.upload_image(current_user.id, file, db)
    return DogImageResponse(profile_image_url=image_url)


@router.put("/", response_model=DogImageResponse)
async def update_dog_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """반려견 프로필 이미지 교체"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_url = await DogImageService.update_image(current_user.id, file, db)
    return DogImageResponse(profile_image_url=image_url)


@router.get("/", response_model=DogImageResponse)
def get_dog_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """반려견 프로필 이미지 URL 조회"""
    image_url = DogImageService.get_image_url(current_user.id, db)
    return DogImageResponse(profile_image_url=image_url)


@router.delete("/", status_code=204)
def delete_dog_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """반려견 프로필 이미지 삭제 (기본 이미지로 변경)"""
    DogImageService.delete_image(current_user.id, db)
    return

from typing import Dict

from core.security import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.food import (
    FoodFeedbackCreate,
    FoodFeedbackResponse,
    FoodProductResponse,
    FoodRecommendationResponse,
)

# services.food_service import를 지연 import로 변경
from sqlalchemy.orm import Session

router = APIRouter(prefix="/food", tags=["food"])


@router.get("/health")
def health_check():
    """Food 라우터 헬스체크"""
    return {"status": "ok", "message": "Food router is working"}


@router.get("/dogs/{dog_id}/recommendations", response_model=FoodRecommendationResponse)
def get_dog_food_recommendations(
    dog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    반려견 맞춤 사료 추천
    - 반려견의 기본 정보, 알러지, 질병, 건강 기록을 분석
    - Food_Recommender 모듈로 최적 사료 추천
    - 추천 결과를 DB에 저장 및 클라이언트에 반환
    """
    try:
        from services.food_service import FoodRecommendationService

        service = FoodRecommendationService(db)
        result = service.get_recommendations(dog_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"추천 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/feedback", response_model=FoodFeedbackResponse)
def create_food_feedback(
    feedback_data: FoodFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    사료 평점 등록 (간단한 별점 시스템)
    - 평점 (1.0~5.0, 0.5 단위)
    """
    try:
        from services.food_service import create_feedback

        feedback = create_feedback(db, current_user, feedback_data)
        return feedback
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"피드백 등록 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/products", response_model=Dict)
def list_food_products(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    db: Session = Depends(get_db),
):
    """
    사료 제품 목록 조회 (클라이언트용 리스트)
    - 페이지네이션 지원
    - 추천 기능과 별도로 사료 제품 정보 제공
    """
    try:
        from services.food_service import get_food_products

        result = get_food_products(db, page, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"제품 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

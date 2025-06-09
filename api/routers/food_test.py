from typing import Dict

from core.security import get_current_user
from db.models import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(tags=["food"])


@router.get("/health")
def health_check():
    """Food 라우터 헬스체크"""
    return {"status": "ok", "message": "Food router is working"}


@router.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    """DB 연결 테스트"""
    try:
        from sqlalchemy import text

        # 간단한 쿼리로 DB 연결 확인
        result = db.execute(text("SELECT 1")).scalar()
        return {"status": "ok", "db_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {str(e)}")


@router.get("/test-auth")
def test_auth(current_user: User = Depends(get_current_user)):
    """인증 테스트"""
    return {"status": "ok", "user_id": current_user.id, "email": current_user.email}


@router.get("/test-recommender")
def test_recommender():
    """추천 모듈 import 테스트"""
    try:
        from foodrecomender.Food_Recommender import ComprehensiveOptimizer

        optimizer = ComprehensiveOptimizer()
        return {"status": "ok", "message": "ComprehensiveOptimizer import successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 모듈 import 실패: {str(e)}")


@router.get("/test-service")
def test_service(db: Session = Depends(get_db)):
    """FoodRecommendationService import 테스트"""
    try:
        from services.food_service import FoodRecommendationService

        service = FoodRecommendationService(db)
        return {
            "status": "ok",
            "message": "FoodRecommendationService import successful",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서비스 import 실패: {str(e)}")


@router.get("/recommend/{dog_id}")
def recommend_food(
    dog_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """특정 반려견에게 사료 추천"""
    try:
        from services.food_service import FoodRecommendationService

        service = FoodRecommendationService(db)
        recommendations = service.get_recommendations(dog_id, current_user.id)

        return {
            "status": "success",
            "dog_id": dog_id,
            "recommendations": recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사료 추천 실패: {str(e)}")


@router.get("/recommendations/current")
def get_current_recommendations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """현재 사용자의 모든 반려견에 대한 사료 추천"""
    try:
        from services.food_service import FoodRecommendationService

        service = FoodRecommendationService(db)
        all_recommendations = service.get_all_recommendations(current_user.id)

        return {
            "status": "success",
            "user_id": current_user.id,
            "recommendations": all_recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 조회 실패: {str(e)}")

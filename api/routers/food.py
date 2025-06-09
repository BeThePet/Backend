from typing import Dict

from core.security import get_current_user
from db.models import Dog, FoodProduct, User
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


@router.get("/recommend-current")
def recommend_for_current_user(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """현재 사용자의 강아지에 대한 새로운 사료 추천 생성"""
    try:
        from services.food_service import FoodRecommendationService

        # 현재 사용자의 강아지 조회 (한 마리 가정)
        dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()

        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        service = FoodRecommendationService(db)
        recommendations = service.get_recommendations(dog.id, current_user.id)

        return {
            "status": "success",
            "dog_id": dog.id,
            "dog_name": dog.name,
            "recommendations": recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사료 추천 실패: {str(e)}")


@router.get("/recommendations/latest")
def get_latest_recommendation(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """현재 사용자의 최신 추천 기록 조회"""
    try:
        from db.models import Dog, FoodRecommendationHistory
        from sqlalchemy import desc

        # 현재 사용자의 강아지 조회
        dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()

        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        # 최신 추천 기록 조회
        latest_recommendation = (
            db.query(FoodRecommendationHistory)
            .filter(FoodRecommendationHistory.dog_id == dog.id)
            .order_by(desc(FoodRecommendationHistory.created_at))
            .first()
        )

        if not latest_recommendation:
            return {
                "status": "success",
                "dog_id": dog.id,
                "dog_name": dog.name,
                "has_recommendation": False,
                "message": "아직 추천 기록이 없습니다.",
            }

        return {
            "status": "success",
            "dog_id": dog.id,
            "dog_name": dog.name,
            "has_recommendation": True,
            "recommendation_id": latest_recommendation.id,
            "last_recommended_at": latest_recommendation.created_at.isoformat(),
            "confidence_score": latest_recommendation.confidence_score,
            "total_recommendations": len(latest_recommendation.recommendations),
            "recommendations": latest_recommendation.recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 조회 실패: {str(e)}")


@router.get("/products")
def list_food_products(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: str = Query(None, description="검색어 (제품명 또는 브랜드)"),
    db: Session = Depends(get_db),
):
    """
    사료 제품 전체 조회 (간단한 정보만)
    - 페이지네이션 지원
    - 검색 기능 지원 (제품명, 브랜드)
    - 반환: 이름, 브랜드, 가격, is_matched만
    """
    try:
        # 기본 쿼리
        query = db.query(FoodProduct).filter(FoodProduct.product_name.isnot(None))

        # 검색어가 있으면 필터링
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (FoodProduct.product_name.ilike(search_filter))
                | (FoodProduct.brand.ilike(search_filter))
            )

        # 총 개수 계산
        total_count = query.count()

        # 페이지네이션 적용
        offset = (page - 1) * limit
        products = query.offset(offset).limit(limit).all()

        # 간단한 정보만 반환
        simplified_products = []
        for product in products:
            simplified_products.append(
                {
                    "id": product.id,
                    "product_name": product.product_name,
                    "brand": product.brand,
                    "price": product.price,
                    "is_matched": product.csv_index
                    is not None,  # csv_index가 있으면 추천 가능
                }
            )

        return {
            "status": "success",
            "products": simplified_products,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total_count": total_count,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": page * limit < total_count,
                "has_prev": page > 1,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제품 조회 실패: {str(e)}")


@router.get("/products/{product_id}")
def get_food_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    사료 제품 상세 조회
    - 모든 영양소 정보, 성분, URL 등 상세 정보 제공
    """
    try:
        product = db.query(FoodProduct).filter(FoodProduct.id == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

        # 상세 정보 반환
        return {
            "status": "success",
            "product": {
                "id": product.id,
                "csv_index": product.csv_index,
                "product_name": product.product_name,
                "brand": product.brand,
                "price": product.price,
                "url": product.url,
                "ingredients": product.ingredients,
                "calorie_content": product.calorie_content,
                # 영양소 정보
                "nutrition": {
                    "protein_pct": product.protein_pct,
                    "fat_pct": product.fat_pct,
                    "fiber_pct": product.fiber_pct,
                    "moisture_pct": product.moisture_pct,
                    "calcium_pct": product.calcium_pct,
                    "phosphorus_pct": product.phosphorus_pct,
                    "sodium_pct": product.sodium_pct,
                    "omega_6_pct": product.omega_6_pct,
                    "omega_3_pct": product.omega_3_pct,
                },
                # 메타 정보
                "meta": {
                    "is_matched": product.csv_index is not None,
                    "can_recommend": product.csv_index is not None,
                    "created_at": (
                        product.created_at.isoformat() if product.created_at else None
                    ),
                    "updated_at": (
                        product.updated_at.isoformat() if product.updated_at else None
                    ),
                },
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제품 상세 조회 실패: {str(e)}")

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

# 프로젝트 루트를 sys.path에 추가하여 foodrecomender 모듈을 찾을 수 있도록 함
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from core.breed_data import get_breed_size_group
from core.disease_mapping import map_diseases_ko_to_en
from db.models import (
    Allergy,
    Disease,
    Dog,
    DogAllergy,
    DogDisease,
    FoodFeedback,
    FoodProduct,
    FoodRecommendationHistory,
    FoodRecord,
    User,
    WalkRecord,
    WaterIntake,
    WeightRecord,
)
from foodrecomender.Food_Recommender import ComprehensiveOptimizer
from schemas.food import FoodFeedbackCreate


class FoodRecommendationService:
    """
    DB 데이터를 Food_Recommender 모듈이 요구하는 형식으로 변환하고,
    추천 결과를 받아 DB에 저장한 후 클라이언트에 전달하는 역할.
    """

    def __init__(self, db: Session):
        self.db = db
        # 데이터 디렉토리 설정 (API 폴더 내 foodrecomender)
        data_dir = Path(__file__).parent.parent / "foodrecomender" / "data"
        # ComprehensiveOptimizer 인스턴스 생성
        self.recommender = ComprehensiveOptimizer(data_dir=data_dir)

    def get_recommendations(self, dog_id: int, user_id: int) -> Dict[str, Any]:
        """메인 추천 로직 실행"""
        dog = self._get_dog(dog_id, user_id)

        # 1. 데이터 준비
        pet_data = self._prepare_pet_data(dog)
        diseases = self._prepare_diseases(dog_id)
        realtime_data = self._prepare_realtime_data(dog_id, dog.weight)

        # 2. ComprehensiveOptimizer 모듈 호출 (JSON 형태로 직접 반환됨)
        request_data = {
            "pet_data": pet_data,
            "diseases": diseases,
            "realtime_data": realtime_data,
        }

        recommendation_result = self.recommender.recommend_from_request(
            request_data, top_n=10
        )

        if recommendation_result["status"] != "success":
            raise ValueError(
                f"추천 실패: {recommendation_result.get('error_message', 'Unknown error')}"
            )

        # 3. 추천 결과에서 CSV 정보 추출
        csv_recommendations = recommendation_result["recommendations"]

        # 4. CSV 추천 결과를 DB 정보와 매칭
        enriched_recommendations = self._enrich_recommendations_with_db_data(
            csv_recommendations
        )

        # 5. 신뢰도 점수 계산 (ComprehensiveOptimizer의 메서드 사용)
        confidence_score = self.recommender.calculate_ml_confidence(
            realtime_data=realtime_data, feedback_history=None
        )

        # 6. DB에 추천 결과 저장
        history_record = FoodRecommendationHistory(
            user_id=user_id,
            dog_id=dog_id,
            pet_data=pet_data,
            diseases=diseases,
            realtime_data=realtime_data,
            recommendations=enriched_recommendations,
            algorithm_version="v1.0",
            confidence_score=confidence_score,
        )
        self.db.add(history_record)
        self.db.commit()
        self.db.refresh(history_record)

        return {
            "recommendation_id": history_record.id,
            "request_conditions": {
                "pet_data": pet_data,
                "diseases": diseases,
                "realtime_data": realtime_data,
            },
            "recommendations": enriched_recommendations,
            "algorithm_version": "v1.0",
            "confidence_score": confidence_score,
            "total_count": len(enriched_recommendations),
        }

    def get_all_recommendations(self, user_id: int) -> Dict[str, Any]:
        """현재 사용자의 모든 반려견에 대한 최신 추천 조회"""
        # 사용자의 모든 반려견 조회
        dogs = self.db.query(Dog).filter(Dog.user_id == user_id).all()

        if not dogs:
            return {"user_id": user_id, "dogs": [], "total_dogs": 0}

        results = []
        for dog in dogs:
            # 각 반려견의 최신 추천 기록 조회
            latest_recommendation = (
                self.db.query(FoodRecommendationHistory)
                .filter(FoodRecommendationHistory.dog_id == dog.id)
                .order_by(desc(FoodRecommendationHistory.created_at))
                .first()
            )

            dog_data = {
                "dog_id": dog.id,
                "dog_name": dog.name,
                "breed": dog.breed_id,
                "has_recommendation": latest_recommendation is not None,
            }

            if latest_recommendation:
                dog_data.update(
                    {
                        "recommendation_id": latest_recommendation.id,
                        "last_recommended_at": latest_recommendation.created_at.isoformat(),
                        "confidence_score": latest_recommendation.confidence_score,
                        "total_recommendations": len(
                            latest_recommendation.recommendations
                        ),
                        "top_3_recommendations": latest_recommendation.recommendations[
                            :3
                        ],  # 상위 3개만
                    }
                )

            results.append(dog_data)

        return {"user_id": user_id, "dogs": results, "total_dogs": len(dogs)}

    def _get_dog(self, dog_id: int, user_id: int) -> Dog:
        """반려견 정보 조회 (소유권 확인 포함)"""
        dog = (
            self.db.query(Dog).filter(Dog.id == dog_id, Dog.user_id == user_id).first()
        )

        if not dog:
            raise ValueError("반려견 정보를 찾을 수 없거나 접근 권한이 없습니다.")

        return dog

    def _prepare_pet_data(self, dog: Dog) -> Dict[str, Any]:
        """DB 데이터를 Food_Recommender가 요구하는 pet_data 형식으로 변환"""

        # 나이 계산 (개월 수)
        age_months = (date.today() - dog.birth_date).days // 30

        # 중성화 여부 확인 (gender 필드에서 '중성화' 포함 여부)
        is_neutered = "중성화" in dog.gender if dog.gender else False

        # 생애 주기 (age_group 컬럼 사용하거나 나이로 계산)
        if hasattr(dog, "age_group") and dog.age_group:
            life_stage = dog.age_group.lower()  # "puppy", "adult", "senior"
        else:
            # age_group이 없으면 나이로 계산
            if age_months < 12:
                life_stage = "puppy"
            elif age_months > 84:
                life_stage = "senior"
            else:
                life_stage = "adult"

        # 품종 크기
        breed_size = get_breed_size_group(dog.breed_id)

        # 알러지 정보
        allergies = [
            allergy.name
            for allergy in self.db.query(Allergy.name)
            .join(DogAllergy, DogAllergy.allergy_id == Allergy.id)
            .filter(DogAllergy.dog_id == dog.id)
            .all()
        ]

        # 활동량 계산 (최근 1주일 산책 횟수 기준)
        one_week_ago = datetime.now() - timedelta(days=7)
        walk_count = (
            self.db.query(func.count(WalkRecord.id))
            .filter(WalkRecord.dog_id == dog.id, WalkRecord.created_at >= one_week_ago)
            .scalar()
        )

        # 산책 횟수에 따른 활동량 분류
        if walk_count >= 14:  # 하루 2회 이상
            activity_level = "high"
        elif walk_count >= 7:  # 하루 1회
            activity_level = "medium"
        else:
            activity_level = "low"

        return {
            "weight_kg": float(dog.weight),
            "age_months": age_months,
            "activity_level": activity_level,
            "is_neutered": is_neutered,
            "life_stage": life_stage,
            "breed_size": breed_size,
            "allergies": allergies,
            # body_condition_score는 생략 (필수값 아님)
        }

    def _prepare_diseases(self, dog_id: int) -> List[str]:
        """반려견의 질병 정보를 영문명으로 변환"""
        korean_diseases = [
            disease.name
            for disease in self.db.query(Disease.name)
            .join(DogDisease, DogDisease.disease_id == Disease.id)
            .filter(DogDisease.dog_id == dog_id)
            .all()
        ]

        # 한글 질병명을 영문으로 매핑
        english_diseases = map_diseases_ko_to_en(korean_diseases)
        return english_diseases

    def _prepare_realtime_data(self, dog_id: int, weight_kg: float) -> Dict[str, Any]:
        """실시간 건강 데이터를 Food_Recommender가 요구하는 형식으로 변환"""

        # 최근 30일 데이터만 조회
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # 체중 이력
        weight_records = (
            self.db.query(WeightRecord)
            .filter(
                WeightRecord.dog_id == dog_id,
                WeightRecord.created_at >= thirty_days_ago,
            )
            .order_by(WeightRecord.created_at)
            .all()
        )

        weight_history = [
            {
                "date": record.created_at.strftime("%Y-%m-%d"),
                "weight_kg": float(record.weight_kg),
            }
            for record in weight_records
        ]

        # 사료 섭취 이력
        food_records = (
            self.db.query(FoodRecord)
            .filter(
                FoodRecord.dog_id == dog_id, FoodRecord.created_at >= thirty_days_ago
            )
            .order_by(FoodRecord.created_at)
            .all()
        )

        intake_history = [
            {
                "date": record.created_at.strftime("%Y-%m-%d"),
                "intake_g": record.amount_g,
            }
            for record in food_records
        ]

        # 활동 이력 (산책)
        walk_records = (
            self.db.query(WalkRecord)
            .filter(
                WalkRecord.dog_id == dog_id, WalkRecord.created_at >= thirty_days_ago
            )
            .order_by(WalkRecord.created_at)
            .all()
        )

        activity_history = [
            {
                "date": record.created_at.strftime("%Y-%m-%d"),
                "minutes": record.duration_min,
            }
            for record in walk_records
        ]

        # 수분 섭취 이력
        water_records = (
            self.db.query(WaterIntake)
            .filter(
                WaterIntake.dog_id == dog_id, WaterIntake.created_at >= thirty_days_ago
            )
            .order_by(WaterIntake.created_at)
            .all()
        )

        water_history = [
            {"date": record.created_at.strftime("%Y-%m-%d"), "ml": record.amount_ml}
            for record in water_records
        ]

        return {
            "weight_history": weight_history,
            "intake_history": intake_history,
            "activity_history": activity_history,
            "water_history": water_history,
        }

    def _enrich_recommendations_with_db_data(
        self, csv_recommendations: List[Dict]
    ) -> List[Dict]:
        """CSV 추천 결과에 DB 정보를 추가하여 클라이언트가 사용할 수 있는 형태로 변환"""
        enriched = []

        for rec in csv_recommendations:
            db_product = None

            # 1차: CSV 인덱스로 정확한 매칭 시도
            csv_index = rec.get("csv_index") or rec.get("index")
            if csv_index is not None:
                try:
                    db_product = (
                        self.db.query(FoodProduct)
                        .filter(FoodProduct.csv_index == int(csv_index))
                        .first()
                    )
                except (ValueError, TypeError):
                    pass

            # 2차: CSV 인덱스 매칭 실패시 제품명/브랜드로 fallback
            if not db_product:
                product_name = rec.get("product_name") or rec.get("Product name")
                brand = rec.get("brand") or rec.get("Brand")

                if product_name and brand:
                    db_product = (
                        self.db.query(FoodProduct)
                        .filter(
                            FoodProduct.product_name.ilike(f"%{product_name}%"),
                            FoodProduct.brand.ilike(f"%{brand}%"),
                        )
                        .first()
                    )
                elif product_name:
                    db_product = (
                        self.db.query(FoodProduct)
                        .filter(FoodProduct.product_name.ilike(f"%{product_name}%"))
                        .first()
                    )

            # CSV 추천 데이터 + DB 정보 결합
            enriched_rec = {
                **rec,  # CSV 추천 결과 (점수, 추천 이유 등)
                "db_product_id": db_product.id if db_product else None,
                "product_url": db_product.url if db_product else None,
                "product_image": None,  # 향후 이미지 필드 추가시 사용
                "is_matched": db_product is not None,
                "match_method": (
                    "csv_index"
                    if csv_index and db_product
                    else "name_brand" if db_product else None
                ),
            }

            enriched.append(enriched_rec)

        # 매칭 통계 로깅
        matched_count = sum(1 for rec in enriched if rec["is_matched"])
        print(
            f"Recommendation matching: {matched_count}/{len(enriched)} products matched"
        )

        return enriched


def create_feedback(
    db: Session, user: User, feedback_data: FoodFeedbackCreate
) -> FoodFeedback:
    """사용자 피드백 생성"""
    # 0.5 단위 체크
    if (feedback_data.rating * 2) % 1 != 0:
        raise ValueError("평점은 0.5 단위로만 입력 가능합니다.")

    # 소유권 확인
    dog = (
        db.query(Dog)
        .filter(Dog.id == feedback_data.dog_id, Dog.user_id == user.id)
        .first()
    )

    if not dog:
        raise ValueError("해당 반려견에 대한 접근 권한이 없습니다.")

    db_feedback = FoodFeedback(**feedback_data.dict(), user_id=user.id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_food_products(db: Session, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """사료 제품 목록 조회 (클라이언트용)"""
    offset = (page - 1) * limit

    foods = db.query(FoodProduct).offset(offset).limit(limit).all()
    total_count = db.query(func.count(FoodProduct.id)).scalar()

    return {
        "foods": foods,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit,
    }

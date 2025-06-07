#!/usr/bin/env python3
"""
리포트 API 테스트용 더미 데이터 생성 스크립트
실행 전에 마이그레이션이 완료되어야 합니다.

실행 방법:
  cd /path/to/BethePet_APP
  python -m api.scripts.create_test_data
"""

import os
import sys
from datetime import date, datetime, time, timedelta

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from api.core.security import get_password_hash
from api.db.enums import HealthStatus
from api.db.models import (
    Breed,
    Dog,
    FoodRecord,
    HealthCheck,
    User,
    WalkRecord,
    WaterIntake,
    WeightRecord,
)
from api.db.session import SessionLocal


def create_test_data():
    """테스트용 더미 데이터 생성"""
    db = SessionLocal()

    try:
        print("🚀 더미 데이터 생성 시작...")

        # 1. 테스트 사용자 생성 (이미 있으면 스킵)
        test_user = db.query(User).filter(User.email == "test@bethe.pet").first()
        if not test_user:
            test_user = User(
                email="test@bethe.pet",
                hashed_password=get_password_hash("testpassword"),
                nickname="테스트유저",
            )
            db.add(test_user)
            db.flush()  # ID 생성
            print("✅ 테스트 사용자 생성")
        else:
            print("✅ 기존 테스트 사용자 사용")

        # 2. 견종 생성 (이미 있으면 스킵)
        test_breed = db.query(Breed).filter(Breed.name == "골든 리트리버").first()
        if not test_breed:
            test_breed = Breed(name="골든 리트리버")
            db.add(test_breed)
            db.flush()
            print("✅ 테스트 견종 생성")
        else:
            print("✅ 기존 테스트 견종 사용")

        # 3. 테스트 강아지 생성 (이미 있으면 스킵)
        test_dog = db.query(Dog).filter(Dog.user_id == test_user.id).first()
        if not test_dog:
            test_dog = Dog(
                name="멍멍이",
                birth_date=date(2020, 6, 15),
                age_group="성견",
                weight=25.5,
                gender="남",
                user_id=test_user.id,
                breed_id=test_breed.id,
            )
            db.add(test_dog)
            db.flush()
            print("✅ 테스트 강아지 생성")
        else:
            print("✅ 기존 테스트 강아지 사용")

        # 4. 최근 2주간의 다양한 데이터 생성
        today = datetime.now().date()

        print("📊 건강 체크 데이터 생성 중...")

        # 건강 체크 데이터 (다양한 패턴)
        health_data = [
            # 수면 (수치형)
            {
                "category": "수면",
                "status": None,
                "numeric_value": 8.0,
                "unit": "시간",
                "memo": "숙면",
            },
            {
                "category": "수면",
                "status": None,
                "numeric_value": 6.5,
                "unit": "시간",
                "memo": "조금 부족",
            },
            {
                "category": "수면",
                "status": None,
                "numeric_value": 7.5,
                "unit": "시간",
                "memo": "적정",
            },
            {
                "category": "수면",
                "status": None,
                "numeric_value": 5.0,
                "unit": "시간",
                "memo": "많이 부족",
            },
            # 체온 (수치형)
            {
                "category": "체온",
                "status": None,
                "numeric_value": 38.5,
                "unit": "°C",
                "memo": "정상",
            },
            {
                "category": "체온",
                "status": None,
                "numeric_value": 39.8,
                "unit": "°C",
                "memo": "약간 높음",
            },
            {
                "category": "체온",
                "status": None,
                "numeric_value": 38.2,
                "unit": "°C",
                "memo": "정상",
            },
            # 식욕 (상태형)
            {"category": "식욕", "status": HealthStatus.normal, "memo": "잘 먹음"},
            {
                "category": "식욕",
                "status": HealthStatus.warning,
                "memo": "조금 적게 먹음",
            },
            {"category": "식욕", "status": HealthStatus.normal, "memo": "평소대로"},
            {
                "category": "식욕",
                "status": HealthStatus.abnormal,
                "memo": "거의 안 먹음",
            },
            # 활력 (상태형)
            {"category": "활력", "status": HealthStatus.normal, "memo": "활발함"},
            {"category": "활력", "status": HealthStatus.normal, "memo": "평소와 같음"},
            {"category": "활력", "status": HealthStatus.warning, "memo": "약간 둔함"},
            # 배변상태 (상태형)
            {"category": "배변상태", "status": HealthStatus.normal, "memo": "정상"},
            {
                "category": "배변상태",
                "status": HealthStatus.warning,
                "memo": "약간 무름",
            },
            {"category": "배변상태", "status": HealthStatus.normal, "memo": "정상"},
        ]

        for i, data in enumerate(health_data):
            check_date = today - timedelta(days=i % 14)  # 최근 2주간 분산
            health_check = HealthCheck(
                dog_id=test_dog.id,
                category=data["category"],
                status=data["status"],
                numeric_value=data.get("numeric_value"),
                unit=data.get("unit"),
                memo=data["memo"],
                created_at=datetime.combine(check_date, datetime.now().time()),
            )
            db.add(health_check)

        print("🚶 산책 데이터 생성 중...")

        # 산책 데이터
        walk_data = [
            (3.2, 45),
            (2.1, 30),
            (4.5, 60),
            (1.8, 25),
            (2.8, 35),
            (3.0, 40),
            (2.5, 30),
            (3.8, 50),
            (2.2, 28),
            (4.0, 55),
        ]

        for i, (distance, duration) in enumerate(walk_data):
            walk_date = today - timedelta(days=i)
            walk = WalkRecord(
                dog_id=test_dog.id,
                distance_km=distance,
                duration_min=duration,
                created_at=datetime.combine(walk_date, datetime.now().time()),
            )
            db.add(walk)

        print("🍽️ 사료/물 데이터 생성 중...")

        # 사료 데이터
        for i in range(14):  # 2주간
            feed_date = today - timedelta(days=i)
            food = FoodRecord(
                dog_id=test_dog.id,
                time=time(8, 30),  # 오전 8:30
                brand="로얄캐닌",
                amount_g=120 + (i % 3) * 10,  # 120-140g 변동
                created_at=datetime.combine(feed_date, datetime.now().time()),
            )
            db.add(food)

            # 물 섭취
            water = WaterIntake(
                dog_id=test_dog.id,
                amount_ml=300 + (i % 5) * 20,  # 300-380ml 변동
                created_at=datetime.combine(feed_date, datetime.now().time()),
            )
            db.add(water)

        print("⚖️ 체중 데이터 생성 중...")

        # 체중 데이터 (점진적 변화)
        base_weight = 25.0
        for i in range(5):  # 5회 측정
            weight_date = today - timedelta(days=i * 3)  # 3일마다
            weight_change = i * 0.1  # 점진적 증가
            weight = WeightRecord(
                dog_id=test_dog.id,
                weight_kg=base_weight + weight_change,
                created_at=datetime.combine(weight_date, datetime.now().time()),
            )
            db.add(weight)

        db.commit()

        print("✅ 더미 데이터 생성 완료!")
        print(f"📋 테스트 계정 정보:")
        print(f"   이메일: test@bethe.pet")
        print(f"   비밀번호: testpassword")
        print(f"   강아지: {test_dog.name} (ID: {test_dog.id})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()

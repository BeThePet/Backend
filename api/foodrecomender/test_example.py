#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

# food_model.py를 import하기 위해 경로 추가
sys.path.append(str(Path.cwd()))

from Food_Recommender import ComprehensiveOptimizer


def test_simple_recommendation():
    """새로운 래퍼 함수를 테스트"""

    # 테스트 데이터 (기존과 동일)
    test_data = {
        "pet_data": {
            "weight_kg": 8.5,
            "age_months": 24,
            "is_neuteured": True,
            "life_stage": "adult",
            "breed_size": "small",
            "allergies": ["닭고기"],
        },
        "diseases": ["Joint Disease"],
        "realtime_data": {
            "weight_history": [
                {"date": "2024-05-20", "weight_kg": 8.6},
                {"date": "2024-05-27", "weight_kg": 8.5},
            ],
            "intake_history": [
                {"date": "2024-05-27", "intake_g": 150},
                {"date": "2024-05-28", "intake_g": 155},
                {"date": "2024-05-29", "intake_g": 152},
            ],
            "activity_history": [
                {"date": "2024-05-27", "minutes": 90},
                {"date": "2024-05-28", "minutes": 100},
                {"date": "2024-05-29", "minutes": 95},
            ],
            "water_history": [
                {"date": "2024-05-27", "ml": 300},
                {"date": "2024-05-28", "ml": 320},
                {"date": "2024-05-29", "ml": 310},
            ],
        },
    }

    print("=== 새로운 래퍼 함수 테스트 ===")
    print("입력 데이터:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50)

    try:
        # ComprehensiveOptimizer 인스턴스 생성
        optimizer = ComprehensiveOptimizer()

        # 새로운 래퍼 함수 사용
        print("추천 시스템 실행 중...")
        result = optimizer.recommend_from_request(test_data, top_n=3)

        print(f"\n✅ 추천 완료!")
        print(f"상태: {result['status']}")
        print(f"총 추천 개수: {result['total_count']}")

        if result["status"] == "success":
            print("\n=== 추천 결과 (JSON 형태) ===")

            # 입력 요약 정보
            summary = result["input_summary"]
            print(f"\n📋 입력 요약:")
            print(
                f"   반려견 정보: {summary['pet_weight_kg']}kg, {summary['pet_age_months']}개월, {summary['life_stage']}, {summary['breed_size']}"
            )
            print(f"   알러지: {summary['allergies']}")
            print(f"   질병: {summary['diseases']}")
            print(
                f"   실시간 데이터: {'있음' if summary['has_realtime_data'] else '없음'}"
            )
            print(
                f"   피드백 데이터: {'있음' if summary['has_feedback_data'] else '없음'}"
            )

            # 추천 사료들
            print(f"\n🏆 추천 사료 목록:")
            for rec in result["recommendations"]:
                print(f"\n   {rec['rank']}위: {rec['product_name']}")
                print(f"      브랜드: {rec['brand']}")
                print(f"      가격: ${rec['price']}")
                print(
                    f"      영양성분: 단백질 {rec['protein_pct']}%, 지방 {rec['fat_pct']}%, 섬유질 {rec['fiber_pct']}%"
                )
                print(f"      생애주기: {rec['life_stage']}")

                # 성분 정보 축약
                ingredients = rec["ingredients"]
                if isinstance(ingredients, str) and len(ingredients) > 80:
                    ingredients = ingredients[:80] + "..."
                print(f"      주요 성분: {ingredients}")

            print(f"\n📄 완전한 JSON 응답:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            print(f"❌ 오류 발생: {result['error_message']}")
            print(f"오류 타입: {result['error_type']}")

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        print(f"예외 타입: {type(e).__name__}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_recommendation()

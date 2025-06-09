from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

from db.models import (
    Dog,
    FoodRecord,
    HealthCheck,
    WalkRecord,
    WaterIntake,
    WeightRecord,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.schemas.health import (
    ActivityStatsResponse,
    ComprehensiveReportResponse,
    HealthInsightResponse,
    HealthItemStatsResponse,
)

KST = ZoneInfo("Asia/Seoul")


class ReportService:
    """리포트 생성 전용 서비스 - 프론트엔드의 복잡한 분석 로직을 구현"""

    @staticmethod
    def get_comprehensive_report(dog_id: int, period: str, db: Session):
        """종합 건강 리포트 생성 - 프론트엔드 로직 완전 이식"""
        today = datetime.now(tz=KST).date()

        # 기간 설정
        if period == "week":
            start_date = today - timedelta(days=7)
        elif period == "month":
            start_date = today - timedelta(days=30)
        else:  # "all"
            start_date = today - timedelta(days=365)

        end_date = today

        # 반려견 정보 조회 (견종별 기준 적용을 위해)
        dog = db.query(Dog).filter(Dog.id == dog_id).first()

        # 기간별 데이터 수집
        raw_data = ReportService._collect_period_data(dog_id, start_date, end_date, db)

        # 활동 통계 계산
        activity_stats = ReportService._calculate_detailed_activity_stats(
            raw_data, period
        )

        # 건강 체크 상세 분석 (프론트엔드 로직 이식)
        health_check_details = ReportService._analyze_health_check_items(
            raw_data["health_checks"]
        )

        # 체중 정보 분석
        weight_info = ReportService._analyze_weight_changes(dog_id, db)

        # 종합 건강 점수 계산 (프론트엔드 로직 완전 이식)
        health_insight = ReportService._generate_comprehensive_health_insight(
            activity_stats, health_check_details, weight_info, period, dog
        )

        return ComprehensiveReportResponse(
            period=period,
            start_date=start_date,
            end_date=end_date,
            health_insight=health_insight,
            activity_stats=activity_stats,
            health_check_details=health_check_details,
            current_weight=weight_info.get("current_weight"),
            weight_change=weight_info.get("weight_change"),
            weight_trend=weight_info.get("trend", "stable"),
        )

    @staticmethod
    def _collect_period_data(
        dog_id: int, start_date: date, end_date: date, db: Session
    ) -> Dict[str, List]:
        """지정된 기간의 모든 데이터 수집"""
        return {
            "walk_records": db.query(WalkRecord)
            .filter(
                WalkRecord.dog_id == dog_id,
                func.date(WalkRecord.created_at).between(start_date, end_date),
            )
            .all(),
            "food_records": db.query(FoodRecord)
            .filter(
                FoodRecord.dog_id == dog_id,
                func.date(FoodRecord.created_at).between(start_date, end_date),
            )
            .all(),
            "water_records": db.query(WaterIntake)
            .filter(
                WaterIntake.dog_id == dog_id,
                func.date(WaterIntake.created_at).between(start_date, end_date),
            )
            .all(),
            "health_checks": db.query(HealthCheck)
            .filter(
                HealthCheck.dog_id == dog_id,
                func.date(HealthCheck.created_at).between(start_date, end_date),
            )
            .all(),
        }

    @staticmethod
    def _calculate_detailed_activity_stats(
        raw_data: Dict[str, List], period: str
    ) -> ActivityStatsResponse:
        """활동 통계 상세 계산"""
        walk_records = raw_data["walk_records"]
        food_records = raw_data["food_records"]
        water_records = raw_data["water_records"]
        health_checks = raw_data["health_checks"]

        # 산책 통계
        walk_count = len(walk_records)
        total_walk_distance = sum(r.distance_km for r in walk_records)
        total_walk_duration = sum(r.duration_min for r in walk_records)
        avg_walk_distance = total_walk_distance / walk_count if walk_count > 0 else 0
        avg_walk_duration = total_walk_duration / walk_count if walk_count > 0 else 0

        # 사료 통계
        feed_count = len(food_records)
        total_feed_amount = sum(r.amount_g for r in food_records)
        avg_feed_amount = total_feed_amount / feed_count if feed_count > 0 else 0

        # 물 섭취 통계
        water_count = len(water_records)
        total_water_amount = sum(r.amount_ml for r in water_records)
        avg_water_amount = total_water_amount / water_count if water_count > 0 else 0

        # 건강 체크 통계 (날짜별 카운트)
        # 날짜별로 그룹화하여 고유한 날짜 수 계산
        health_check_dates = set()
        for h in health_checks:
            health_check_dates.add(h.created_at.date())
        health_check_count = len(health_check_dates)

        health_check_abnormal_count = len(
            [
                h
                for h in health_checks
                if h.status is not None and h.status.value in ["주의", "이상"]
            ]
        )

        return ActivityStatsResponse(
            walk_count=walk_count,
            avg_walk_distance=round(avg_walk_distance, 2),
            avg_walk_duration=round(avg_walk_duration, 1),
            total_walk_distance=round(total_walk_distance, 2),
            total_walk_duration=total_walk_duration,
            feed_count=feed_count,
            avg_feed_amount=round(avg_feed_amount, 1),
            total_feed_amount=total_feed_amount,
            water_count=water_count,
            avg_water_amount=round(avg_water_amount, 1),
            total_water_amount=total_water_amount,
            health_check_count=health_check_count,
            health_check_abnormal_count=health_check_abnormal_count,
        )

    @staticmethod
    def _analyze_health_check_items(
        health_checks: List[HealthCheck],
    ) -> List[HealthItemStatsResponse]:
        """건강 체크 항목별 세밀한 분석 - 프론트엔드 로직 이식"""
        if not health_checks:
            return []

        # 카테고리별로 그룹화
        categories = {}
        for check in health_checks:
            category = check.category
            if category not in categories:
                categories[category] = []
            categories[category].append(check)

        details = []
        for category, checks in categories.items():
            detail = ReportService._analyze_health_check_item(category, checks)
            details.append(detail)

        return details

    @staticmethod
    def _analyze_health_check_item(
        category: str, checks: List[HealthCheck]
    ) -> HealthItemStatsResponse:
        """개별 건강 체크 항목 분석 - 프론트엔드의 analyzeHealthCheckItem 로직 이식"""
        count = len(checks)

        # 수치형 데이터 처리 (수면, 체온 등) - 새로운 numeric_value 필드 사용
        if category in ["수면", "체온"]:
            numeric_checks = [c for c in checks if c.numeric_value is not None]

            if numeric_checks:
                values = [c.numeric_value for c in numeric_checks]
                average = sum(values) / len(values)
                unit = numeric_checks[0].unit or (
                    "시간" if category == "수면" else "°C"
                )

                # 수치 기반 상태 평가
                if category == "수면":
                    if average < 4:
                        status = "이상"
                        explanation = f"평균 수면 시간이 {round(average, 1)}시간으로 매우 부족합니다."
                    elif average < 6:
                        status = "주의"
                        explanation = f"평균 수면 시간이 {round(average, 1)}시간으로 다소 부족합니다."
                    else:
                        status = "정상"
                        explanation = f"평균 수면 시간이 {round(average, 1)}시간으로 적정 수준입니다."
                elif category == "체온":
                    if average > 40 or average < 37:
                        status = "이상"
                        explanation = (
                            f"평균 체온이 {round(average, 1)}°C로 위험 수준입니다."
                        )
                    elif average > 39.2 or average < 37.5:
                        status = "주의"
                        explanation = f"평균 체온이 {round(average, 1)}°C로 정상 범위를 벗어났습니다."
                    else:
                        status = "정상"
                        explanation = f"평균 체온이 {round(average, 1)}°C로 정상 범위 내에 있습니다."

                return HealthItemStatsResponse(
                    category=category,
                    count=count,
                    status=status,
                    average_value=round(average, 1),
                    unit=unit,
                    explanation=explanation,
                )

                # 상태형 데이터 처리 (식욕, 활력, 배변상태 등) - null status 처리
        status_checks = [c for c in checks if c.status is not None]

        if not status_checks:
            # 모든 데이터가 수치형인 경우
            return HealthItemStatsResponse(
                category=category,
                count=count,
                status="정상",
                explanation=f"{category} 데이터가 수치형으로만 기록되어 상태 분석이 불가능합니다.",
            )

        normal_count = len([c for c in status_checks if c.status.value == "정상"])
        warning_count = len([c for c in status_checks if c.status.value == "주의"])
        abnormal_count = len([c for c in status_checks if c.status.value == "이상"])

        # 비정상 비율 계산 (주의 + 이상)
        problematic_count = warning_count + abnormal_count
        status_count = len(status_checks)
        abnormal_ratio = problematic_count / status_count if status_count > 0 else 0

        # 상태 평가 로직
        if abnormal_count > 0:  # 이상이 하나라도 있으면 경고
            status = "이상"
            explanation = f"이상 상태가 {abnormal_count}회, 주의 상태가 {warning_count}회 발견되었습니다."
        elif warning_count >= status_count * 0.3:  # 주의가 30% 이상이면 경고
            status = "주의"
            explanation = f"주의 상태가 {round(warning_count/status_count * 100)}%로 주의가 필요합니다."
        else:
            status = "정상"
            explanation = "대체로 정상 상태를 유지하고 있습니다."

        # 항목별 특수 분석 (프론트엔드 로직 이식)
        if category == "식욕":
            # memo에서 특수 상태 카운트 (실제 구현시 적절한 필드 사용)
            less_count = len([c for c in checks if c.memo and "적게" in c.memo])
            none_count = len([c for c in checks if c.memo and "없음" in c.memo])

            if none_count > 0:
                explanation += f" 식사를 전혀 하지 않은 날이 {none_count}일 있었습니다."
            elif less_count > 0:
                explanation += f" 식사량이 적은 날이 {less_count}일 있었습니다."

        elif category == "배변상태":
            soft_count = len([c for c in checks if c.memo and "무른" in c.memo])
            none_count = len([c for c in checks if c.memo and "없음" in c.memo])
            abnormal_count_special = len(
                [c for c in checks if c.memo and "비정상" in c.memo]
            )

            if abnormal_count_special > 0:
                explanation += f" 비정상 배변이 {abnormal_count_special}회 있었습니다."
            elif none_count > 0:
                explanation += f" 배변이 없었던 날이 {none_count}일 있었습니다."
            elif soft_count > 0:
                explanation += f" 무른 변이 {soft_count}회 있었습니다."

        return HealthItemStatsResponse(
            category=category,
            count=count,
            status=status,
            normal_count=normal_count,
            abnormal_count=problematic_count,
            abnormal_ratio=f"{round(abnormal_ratio * 100)}%",
            explanation=explanation,
        )

    @staticmethod
    def _analyze_weight_changes(dog_id: int, db: Session) -> Dict[str, Any]:
        """체중 변화 분석"""
        weight_records = (
            db.query(WeightRecord)
            .filter(WeightRecord.dog_id == dog_id)
            .order_by(WeightRecord.created_at.desc())
            .limit(2)  # 최근 2개만
            .all()
        )

        if not weight_records:
            return {"current_weight": None, "weight_change": 0, "trend": "stable"}

        current_weight = weight_records[0].weight_kg

        if len(weight_records) < 2:
            return {
                "current_weight": current_weight,
                "weight_change": 0,
                "trend": "stable",
            }

        previous_weight = weight_records[1].weight_kg
        weight_change = round(current_weight - previous_weight, 1)

        # 트렌드 결정 (프론트엔드 로직 이식)
        if weight_change > 0.2:
            trend = "up"
        elif weight_change < -0.2:
            trend = "down"
        else:
            trend = "stable"

        return {
            "current_weight": current_weight,
            "weight_change": weight_change,
            "trend": trend,
        }

    @staticmethod
    def _generate_comprehensive_health_insight(
        activity_stats: ActivityStatsResponse,
        health_check_details: List[HealthItemStatsResponse],
        weight_info: Dict[str, Any],
        period: str,
        dog: Dog,
    ) -> HealthInsightResponse:
        """종합 건강 인사이트 생성 - 프론트엔드 로직 완전 이식"""

        # 프론트엔드의 calculateComprehensiveHealthScore 로직 이식
        score = 100
        score_breakdown = []

        # 건강 체크 항목별 세밀한 감점 (프론트엔드 로직)
        for detail in health_check_details:
            if detail.category == "식욕":
                if detail.status == "주의":
                    score -= 8
                    score_breakdown.append("식욕 주의(-8)")
                elif detail.status == "이상":
                    score -= 15
                    score_breakdown.append("식욕 이상(-15)")
            elif detail.category == "활력":
                if detail.status == "주의":
                    score -= 8
                    score_breakdown.append("활력 주의(-8)")
                elif detail.status == "이상":
                    score -= 15
                    score_breakdown.append("활력 이상(-15)")
            elif detail.category == "배변상태":
                if detail.status == "주의":
                    score -= 10
                    score_breakdown.append("배변 주의(-10)")
                elif detail.status == "이상":
                    score -= 20
                    score_breakdown.append("배변 이상(-20)")
            elif detail.category == "수면":
                if detail.status == "주의":
                    score -= 5
                    score_breakdown.append("수면 주의(-5)")
                elif detail.status == "이상":
                    score -= 10
                    score_breakdown.append("수면 이상(-10)")
            elif detail.category == "체온":
                if detail.status == "주의":
                    score -= 10
                    score_breakdown.append("체온 주의(-10)")
                elif detail.status == "이상":
                    score -= 25
                    score_breakdown.append("체온 이상(-25)")

        # 활동 기반 세밀한 감점/가점 (프론트엔드 로직)
        if activity_stats.walk_count < 3:
            score -= 5
            score_breakdown.append("산책 부족(-5)")
        elif activity_stats.walk_count >= 5:
            score += 5
            score_breakdown.append("산책 우수(+5)")

        # 사료 급여 평가 (프론트엔드 로직)
        expected_feeds = 7 if period == "week" else 30 if period == "month" else 90
        if activity_stats.feed_count < expected_feeds:
            feed_deduction = min(10, (expected_feeds - activity_stats.feed_count) * 2)
            score -= feed_deduction
            score_breakdown.append(f"사료 급여 부족(-{feed_deduction})")

        # 물 섭취 평가 (프론트엔드 로직)
        expected_water = 7 if period == "week" else 30 if period == "month" else 90
        if activity_stats.water_count < expected_water:
            water_deduction = min(15, (expected_water - activity_stats.water_count) * 3)
            score -= water_deduction
            score_breakdown.append(f"물 섭취 부족(-{water_deduction})")

        # 점수 범위 조정
        score = max(10, min(100, score))

        # 상태 결정
        if score >= 80:
            status = "매우 좋음"
        elif score >= 60:
            status = "주의 필요"
        else:
            status = "관리 필요"

        # 인사이트 메시지 생성 (프론트엔드의 generateComprehensiveInsight 로직 이식)
        insights = ReportService._generate_detailed_insights(
            activity_stats, health_check_details, weight_info, period, dog, status
        )

        if not score_breakdown:
            score_breakdown.append("감점 요소가 없습니다.")

        return HealthInsightResponse(
            score=score,
            status=status,
            insights=insights,
            score_breakdown=score_breakdown,
        )

    @staticmethod
    def _generate_detailed_insights(
        activity_stats: ActivityStatsResponse,
        health_check_details: List[HealthItemStatsResponse],
        weight_info: Dict[str, Any],
        period: str,
        dog: Dog,
        status: str,
    ) -> List[str]:
        """상세 인사이트 메시지 생성 - 프론트엔드 로직 완전 이식"""
        insights = []

        # 기간별 메시지
        period_text = (
            "최근 7일"
            if period == "week"
            else "최근 30일" if period == "month" else "전체 기간"
        )
        insights.append(f"{period_text} 동안의 종합 건강 상태는 '{status}'입니다.")

        # 건강 체크 인사이트
        health_concerns = [
            detail.category
            for detail in health_check_details
            if detail.status != "정상"
        ]

        if health_concerns:
            insights.append(f"{', '.join(health_concerns)}에 주의가 필요합니다.")
        elif health_check_details:
            insights.append("건강 체크 항목에서 특별한 이상은 발견되지 않았습니다.")
        else:
            insights.append(
                "건강 체크 데이터가 아직 수집되지 않았습니다. 정기적인 건강 체크를 통해 더 정확한 인사이트를 받아보세요."
            )

        # 산책 인사이트 (프론트엔드 로직)
        walk_count = activity_stats.walk_count
        if walk_count == 0:
            insights.append(
                "산책 기록이 없습니다. 규칙적인 산책은 반려견의 신체적, 정신적 건강에 중요합니다."
            )
        elif walk_count < 3:
            insights.append(
                f"산책이 {walk_count}회로 다소 부족합니다. 가능하다면 주 3-5회 정도의 산책을 권장합니다."
            )
        elif walk_count >= 5:
            insights.append(
                f"산책을 {walk_count}회 진행했습니다. 규칙적인 산책 습관이 잘 유지되고 있습니다."
            )
        else:
            avg_distance = activity_stats.avg_walk_distance
            insights.append(
                f"산책을 {walk_count}회 진행했습니다. 적정 수준의 산책 횟수입니다. 평균 {avg_distance}km의 거리를 유지하며 꾸준히 산책하세요."
            )

        # 사료 인사이트 (견종별 기준 적용 - 프론트엔드 로직)
        feed_count = activity_stats.feed_count
        if feed_count == 0:
            insights.append(
                "사료 급여 기록이 없습니다. 규칙적인 식사는 반려견의 건강에 중요합니다."
            )
        elif feed_count < 7:
            insights.append(
                f"사료 급여는 {feed_count}회로 기록되었습니다. 매일 규칙적인 식사 기록을 권장합니다."
            )
        else:
            avg_amount = activity_stats.avg_feed_amount
            feed_comment = ReportService._get_breed_specific_feed_comment(
                dog, avg_amount
            )
            insights.append(
                f"사료 급여가 잘 이루어졌습니다. 평균 {int(avg_amount)}g의 사료를 급여했습니다.{feed_comment}"
            )

        # 물 섭취 인사이트
        water_count = activity_stats.water_count
        if water_count == 0:
            insights.append(
                "물 섭취 기록이 없습니다. 충분한 수분 섭취는 반려견의 건강에 필수적입니다."
            )
        elif water_count < 7:
            insights.append(
                f"물 섭취는 {water_count}회로 기록되었습니다. 매일 충분한 수분 섭취를 확인해주세요."
            )
        else:
            total_amount = activity_stats.total_water_amount
            insights.append(
                f"물 섭취가 잘 이루어졌습니다. 총 {total_amount}ml의 물을 섭취했습니다."
            )

        # 체중 인사이트 (견종별 기준 적용 - 프론트엔드 로직)
        if weight_info.get("current_weight"):
            weight_comment = ReportService._get_breed_specific_weight_comment(
                dog, weight_info
            )
            insights.append(weight_comment)

        return insights

    @staticmethod
    def _get_breed_specific_feed_comment(dog: Dog, avg_amount: float) -> str:
        """견종별 사료량 기준 코멘트 - 프론트엔드 로직 이식"""
        # 견종 정보에서 크기 추정 (실제 구현시 Dog 모델에 size 필드 추가 고려)
        dog_size = ReportService._estimate_dog_size(dog)

        if dog_size == "small" and (avg_amount < 30 or avg_amount > 150):
            return " 소형견 기준 사료량(30-150g)을 벗어났습니다. 적정량을 확인해보세요."
        elif dog_size == "medium" and (avg_amount < 100 or avg_amount > 300):
            return (
                " 중형견 기준 사료량(100-300g)을 벗어났습니다. 적정량을 확인해보세요."
            )
        elif dog_size == "large" and (avg_amount < 200 or avg_amount > 500):
            return (
                " 대형견 기준 사료량(200-500g)을 벗어났습니다. 적정량을 확인해보세요."
            )
        return ""

    @staticmethod
    def _get_breed_specific_weight_comment(
        dog: Dog, weight_info: Dict[str, Any]
    ) -> str:
        """견종별 체중 변화 코멘트 - 프론트엔드 로직 이식"""
        dog_size = ReportService._estimate_dog_size(dog)
        weight_change = weight_info["weight_change"]

        # 견종별 체중 변화 기준
        threshold = 1.0 if dog_size == "large" else 0.5

        if weight_change > threshold:
            return f"체중이 {weight_change}kg 증가했습니다. 급격한 체중 증가는 건강에 좋지 않을 수 있으니 식이와 운동량을 확인해보세요."
        elif weight_change < -threshold:
            return f"체중이 {abs(weight_change)}kg 감소했습니다. 급격한 체중 감소는 건강 문제의 신호일 수 있으니 주의 깊게 관찰해주세요."
        else:
            return "체중이 안정적으로 유지되고 있습니다."

    @staticmethod
    def _estimate_dog_size(dog: Dog) -> str:
        """견종/체중 정보로 개체 크기 추정"""
        # 현재 체중으로 크기 추정 (임시 로직)
        if dog.weight <= 10:
            return "small"
        elif dog.weight <= 25:
            return "medium"
        else:
            return "large"

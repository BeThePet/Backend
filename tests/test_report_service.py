"""
리포트 서비스 단위 테스트
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from db.enums import HealthStatus
from db.models import FoodRecord, HealthCheck, WalkRecord, WaterIntake, WeightRecord
from services.report_service import ReportService
from sqlalchemy.orm import Session


class TestReportService:

    @pytest.fixture
    def mock_db(self):
        """Mock 데이터베이스 세션"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def report_service(self, mock_db):
        """리포트 서비스 인스턴스"""
        return ReportService(mock_db)

    @pytest.fixture
    def sample_health_data(self):
        """테스트용 건강 데이터"""
        today = datetime.now()
        return [
            # 수면 데이터 (수치형)
            HealthCheck(
                id=1,
                dog_id=1,
                category="수면",
                numeric_value=8.0,
                unit="시간",
                status=None,
                created_at=today - timedelta(days=1),
            ),
            HealthCheck(
                id=2,
                dog_id=1,
                category="수면",
                numeric_value=6.0,
                unit="시간",
                status=None,
                created_at=today - timedelta(days=2),
            ),
            # 체온 데이터 (수치형)
            HealthCheck(
                id=3,
                dog_id=1,
                category="체온",
                numeric_value=38.5,
                unit="°C",
                status=None,
                created_at=today - timedelta(days=1),
            ),
            # 식욕 데이터 (상태형)
            HealthCheck(
                id=4,
                dog_id=1,
                category="식욕",
                status=HealthStatus.normal,
                numeric_value=None,
                created_at=today - timedelta(days=1),
            ),
            HealthCheck(
                id=5,
                dog_id=1,
                category="식욕",
                status=HealthStatus.warning,
                numeric_value=None,
                created_at=today - timedelta(days=2),
            ),
        ]

    @pytest.fixture
    def sample_activity_data(self):
        """테스트용 활동 데이터"""
        today = datetime.now()
        return {
            "walks": [
                WalkRecord(
                    id=1, dog_id=1, distance_km=3.2, duration_min=45, created_at=today
                ),
                WalkRecord(
                    id=2,
                    dog_id=1,
                    distance_km=2.5,
                    duration_min=30,
                    created_at=today - timedelta(days=1),
                ),
            ],
            "foods": [
                FoodRecord(id=1, dog_id=1, amount_g=120, created_at=today),
                FoodRecord(
                    id=2, dog_id=1, amount_g=130, created_at=today - timedelta(days=1)
                ),
            ],
            "waters": [
                WaterIntake(id=1, dog_id=1, amount_ml=300, created_at=today),
                WaterIntake(
                    id=2, dog_id=1, amount_ml=350, created_at=today - timedelta(days=1)
                ),
            ],
            "weights": [
                WeightRecord(id=1, dog_id=1, weight_kg=25.5, created_at=today),
            ],
        }

    def test_calculate_health_score_numeric_data(
        self, report_service, sample_health_data
    ):
        """수치형 데이터 건강 점수 계산 테스트"""
        # 수면 데이터만 필터링
        sleep_data = [item for item in sample_health_data if item.category == "수면"]

        score = report_service._calculate_health_score(sleep_data)

        # 8시간(90점) + 6시간(70점) = 평균 80점
        assert score == 80

    def test_calculate_health_score_status_data(
        self, report_service, sample_health_data
    ):
        """상태형 데이터 건강 점수 계산 테스트"""
        # 식욕 데이터만 필터링
        appetite_data = [item for item in sample_health_data if item.category == "식욕"]

        score = report_service._calculate_health_score(appetite_data)

        # 정상(90점) + 주의(70점) = 평균 80점
        assert score == 80

    def test_numeric_to_status_conversion_sleep(self, report_service):
        """수면 시간 -> 상태 변환 테스트"""
        assert (
            report_service._convert_numeric_to_status("수면", 8.0)
            == HealthStatus.normal
        )
        assert (
            report_service._convert_numeric_to_status("수면", 6.0)
            == HealthStatus.warning
        )
        assert (
            report_service._convert_numeric_to_status("수면", 4.0)
            == HealthStatus.abnormal
        )

    def test_numeric_to_status_conversion_temperature(self, report_service):
        """체온 -> 상태 변환 테스트"""
        assert (
            report_service._convert_numeric_to_status("체온", 38.5)
            == HealthStatus.normal
        )
        assert (
            report_service._convert_numeric_to_status("체온", 39.5)
            == HealthStatus.warning
        )
        assert (
            report_service._convert_numeric_to_status("체온", 40.5)
            == HealthStatus.abnormal
        )

    def test_generate_insights_with_data(self, report_service, sample_health_data):
        """인사이트 생성 테스트 (데이터 있음)"""
        insights = report_service._generate_insights(sample_health_data)

        assert len(insights) > 0
        assert any("수면" in insight for insight in insights)
        assert any("체온" in insight for insight in insights)

    def test_generate_insights_no_data(self, report_service):
        """인사이트 생성 테스트 (데이터 없음)"""
        insights = report_service._generate_insights([])

        assert len(insights) == 1
        assert "건강 데이터가 부족합니다" in insights[0]

    def test_get_health_status_by_score(self, report_service):
        """점수별 건강 상태 분류 테스트"""
        assert report_service._get_health_status_by_score(95) == "매우 좋음"
        assert report_service._get_health_status_by_score(85) == "좋음"
        assert report_service._get_health_status_by_score(75) == "보통"
        assert report_service._get_health_status_by_score(65) == "주의 필요"
        assert report_service._get_health_status_by_score(45) == "관리 필요"

    @patch("services.report_service.ReportService._get_health_data")
    @patch("services.report_service.ReportService._get_activity_data")
    def test_get_comprehensive_report_week(
        self,
        mock_activity,
        mock_health,
        report_service,
        sample_health_data,
        sample_activity_data,
    ):
        """주간 종합 리포트 생성 테스트"""
        # Mock 데이터 설정
        mock_health.return_value = sample_health_data
        mock_activity.return_value = sample_activity_data

        report = report_service.get_comprehensive_report(dog_id=1, period="week")

        # 결과 검증
        assert "health_insight" in report
        assert "activity_stats" in report
        assert report["health_insight"]["score"] > 0
        assert report["activity_stats"]["walk_count"] == 2

    @patch("services.report_service.ReportService._get_health_data")
    def test_get_health_insight_only(
        self, mock_health, report_service, sample_health_data
    ):
        """건강 인사이트만 조회 테스트"""
        mock_health.return_value = sample_health_data

        insight = report_service.get_health_insight(dog_id=1, period="month")

        assert "score" in insight
        assert "status" in insight
        assert "insights" in insight
        assert len(insight["insights"]) > 0

    @patch("services.report_service.ReportService._get_activity_data")
    def test_get_activity_stats_only(
        self, mock_activity, report_service, sample_activity_data
    ):
        """활동 통계만 조회 테스트"""
        mock_activity.return_value = sample_activity_data

        stats = report_service.get_activity_stats(dog_id=1, period="all")

        assert "walk_count" in stats
        assert "total_walk_distance" in stats
        assert "avg_walk_distance" in stats
        assert "feed_count" in stats
        assert "avg_food_amount" in stats
        assert "avg_water_intake" in stats
        assert "latest_weight" in stats

    def test_period_validation(self, report_service):
        """기간 유효성 검증 테스트"""
        # 유효한 기간들
        valid_periods = ["week", "month", "all"]
        for period in valid_periods:
            # 예외가 발생하지 않아야 함
            try:
                report_service._validate_period(period)
            except ValueError:
                pytest.fail(f"Valid period '{period}' raised ValueError")

        # 무효한 기간
        with pytest.raises(ValueError):
            report_service._validate_period("invalid")

    def test_empty_data_handling(self, report_service):
        """빈 데이터 처리 테스트"""
        # 빈 건강 데이터
        score = report_service._calculate_health_score([])
        assert score == 0

        # 빈 활동 데이터
        stats = report_service._calculate_activity_stats(
            {"walks": [], "foods": [], "waters": [], "weights": []}
        )
        assert stats["walk_count"] == 0
        assert stats["total_walk_distance"] == 0.0
        assert stats["avg_walk_distance"] == 0.0

    def test_null_value_handling(self, report_service):
        """NULL 값 처리 테스트"""
        # status와 numeric_value가 모두 None인 경우
        health_data = [
            HealthCheck(
                id=1,
                dog_id=1,
                category="수면",
                status=None,
                numeric_value=None,
                created_at=datetime.now(),
            )
        ]

        score = report_service._calculate_health_score(health_data)
        assert score == 0  # NULL 데이터는 점수에 포함되지 않음

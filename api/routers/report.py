from typing import List

from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from services.report_service import ReportService
from sqlalchemy.orm import Session

from api.schemas.health import (
    ActivityStatsResponse,
    ComprehensiveReportResponse,
    HealthInsightResponse,
    HealthItemStatsResponse,
)

router = APIRouter()


def get_dog_or_404(user_id: int, db: Session):
    dog = db.query(Dog).filter(Dog.user_id == user_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    return dog


@router.get("/comprehensive", response_model=ComprehensiveReportResponse)
async def get_comprehensive_report(
    period: str = "week",  # week, month, all
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """종합 건강 리포트 조회 - 프론트엔드의 복잡한 분석 로직을 백엔드로 이식"""

    if period not in ["week", "month", "all"]:
        raise HTTPException(
            status_code=400, detail="기간은 'week', 'month', 'all' 중 하나여야 합니다."
        )

    dog = get_dog_or_404(current_user.id, db)

    try:
        return ReportService.get_comprehensive_report(dog.id, period, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/insight", response_model=HealthInsightResponse)
async def get_health_insight(
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """건강 인사이트만 조회"""

    if period not in ["week", "month", "all"]:
        raise HTTPException(
            status_code=400, detail="기간은 'week', 'month', 'all' 중 하나여야 합니다."
        )

    dog = get_dog_or_404(current_user.id, db)

    try:
        comprehensive_report = ReportService.get_comprehensive_report(
            dog.id, period, db
        )
        return comprehensive_report.health_insight
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"인사이트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/activities", response_model=ActivityStatsResponse)
async def get_activity_stats(
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """활동 통계만 조회"""

    if period not in ["week", "month", "all"]:
        raise HTTPException(
            status_code=400, detail="기간은 'week', 'month', 'all' 중 하나여야 합니다."
        )

    dog = get_dog_or_404(current_user.id, db)

    try:
        comprehensive_report = ReportService.get_comprehensive_report(
            dog.id, period, db
        )
        return comprehensive_report.activity_stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"활동 통계 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health-details", response_model=List[HealthItemStatsResponse])
async def get_health_check_details(
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """건강 체크 항목별 상세 분석만 조회"""

    if period not in ["week", "month", "all"]:
        raise HTTPException(
            status_code=400, detail="기간은 'week', 'month', 'all' 중 하나여야 합니다."
        )

    dog = get_dog_or_404(current_user.id, db)

    try:
        comprehensive_report = ReportService.get_comprehensive_report(
            dog.id, period, db
        )
        return comprehensive_report.health_check_details
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"건강 체크 상세 분석 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/summary")
async def get_report_summary(
    period: str = "week",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """리포트 요약 정보 (점수와 상태만)"""

    if period not in ["week", "month", "all"]:
        raise HTTPException(
            status_code=400, detail="기간은 'week', 'month', 'all' 중 하나여야 합니다."
        )

    dog = get_dog_or_404(current_user.id, db)

    try:
        comprehensive_report = ReportService.get_comprehensive_report(
            dog.id, period, db
        )

        return {
            "period": period,
            "health_score": comprehensive_report.health_insight.score,
            "health_status": comprehensive_report.health_insight.status,
            "walk_count": comprehensive_report.activity_stats.walk_count,
            "feed_count": comprehensive_report.activity_stats.feed_count,
            "health_check_count": comprehensive_report.activity_stats.health_check_count,
            "abnormal_health_count": comprehensive_report.activity_stats.health_check_abnormal_count,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"리포트 요약 생성 중 오류가 발생했습니다: {str(e)}"
        )

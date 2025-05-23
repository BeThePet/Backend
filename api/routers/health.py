from datetime import date
from typing import List

from core.security import get_current_user
from db.models import Dog, User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.health import (
    FoodRecordCreate,
    FoodRecordResponse,
    HealthDailyCreate,
    HealthDailyResponse,
    WalkRecordCreate,
    WalkRecordResponse,
    WaterRecordCreate,
    WaterRecordResponse,
    WeeklyReportResponse,
    WeightRecordCreate,
    WeightRecordResponse,
)
from api.services.health_service import HealthService

router = APIRouter()


def get_dog_or_404(current_user: User, db: Session):
    dog = db.query(Dog).filter(Dog.user_id == current_user.id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="반려견 정보가 없습니다")
    return dog


# HealthDaily
@router.post("/", response_model=HealthDailyResponse)
def create_health_daily(
    payload: HealthDailyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.create_health_daily_record(dog.id, payload, db)


@router.get("/", response_model=List[HealthDailyResponse])
def list_health_daily(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.list_health_daily_records(dog.id, db)


@router.get("/{record_id}", response_model=HealthDailyResponse)
def get_health_daily(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.get_health_daily_record(record_id, current_user.id, db)


@router.put("/{record_id}", response_model=HealthDailyResponse)
def update_health_daily(
    record_id: int,
    payload: HealthDailyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.update_health_daily_record(
        record_id, current_user.id, payload, db
    )


@router.delete("/{record_id}", status_code=204)
def delete_health_daily(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    HealthService.delete_health_daily_record(record_id, current_user.id, db)


# Walk
@router.post("/walks", response_model=WalkRecordResponse)
def create_walk(
    payload: WalkRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.create_walk_record(dog.id, payload, db)


@router.get("/walks", response_model=List[WalkRecordResponse])
def list_walks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.list_walk_records(dog.id, db)


@router.get("/walks/{record_id}", response_model=WalkRecordResponse)
def get_walk(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.get_walk_record(record_id, current_user.id, db)


@router.put("/walks/{record_id}", response_model=WalkRecordResponse)
def update_walk(
    record_id: int,
    payload: WalkRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.update_walk_record(record_id, current_user.id, payload, db)


@router.delete("/walks/{record_id}", status_code=204)
def delete_walk(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    HealthService.delete_walk_record(record_id, current_user.id, db)


# Food
@router.post("/foods", response_model=FoodRecordResponse)
def create_food(
    payload: FoodRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.create_food_record(dog.id, payload, db)


@router.get("/foods", response_model=List[FoodRecordResponse])
def list_foods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.list_food_records(dog.id, db)


@router.get("/foods/{record_id}", response_model=FoodRecordResponse)
def get_food(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.get_food_record(record_id, current_user.id, db)


@router.put("/foods/{record_id}", response_model=FoodRecordResponse)
def update_food(
    record_id: int,
    payload: FoodRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.update_food_record(record_id, current_user.id, payload, db)


@router.delete("/foods/{record_id}", status_code=204)
def delete_food(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    HealthService.delete_food_record(record_id, current_user.id, db)


# Water
@router.post("/waters", response_model=WaterRecordResponse)
def create_water(
    payload: WaterRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.create_water_record(dog.id, payload, db)


@router.get("/waters", response_model=List[WaterRecordResponse])
def list_waters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.list_water_records(dog.id, db)


@router.get("/waters/{record_id}", response_model=WaterRecordResponse)
def get_water(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.get_water_record(record_id, current_user.id, db)


@router.put("/waters/{record_id}", response_model=WaterRecordResponse)
def update_water(
    record_id: int,
    payload: WaterRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.update_water_record(record_id, current_user.id, payload, db)


@router.delete("/waters/{record_id}", status_code=204)
def delete_water(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    HealthService.delete_water_record(record_id, current_user.id, db)


# Weight
@router.post("/weights", response_model=WeightRecordResponse)
def create_weight(
    payload: WeightRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.create_weight_record(dog.id, payload, db)


@router.get("/weights", response_model=List[WeightRecordResponse])
def list_weights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.list_weight_records(dog.id, db)


@router.get("/weights/{record_id}", response_model=WeightRecordResponse)
def get_weight(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.get_weight_record(record_id, current_user.id, db)


@router.put("/weights/{record_id}", response_model=WeightRecordResponse)
def update_weight(
    record_id: int,
    payload: WeightRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return HealthService.update_weight_record(record_id, current_user.id, payload, db)


@router.delete("/weights/{record_id}", status_code=204)
def delete_weight(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    HealthService.delete_weight_record(record_id, current_user.id, db)


# Weekly_report
@router.get("/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dog = get_dog_or_404(current_user, db)
    return HealthService.get_weekly_report(dog.id, db)

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from db.models import (
    FoodRecord,
    HealthCheck,
    WalkRecord,
    WaterIntake,
    WeightRecord,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.schemas.health import (
    FoodRecordCreate,
    HealthDailyCreate,
    WalkRecordCreate,
    WaterRecordCreate,
    WeeklyReportResponse,
    WeightRecordCreate,
)

KST = ZoneInfo("Asia/Seoul")


class HealthService:

    @staticmethod
    def create_health_daily_record(dog_id: int, data: HealthDailyCreate, db: Session):
        existing = (
            db.query(HealthCheck)
            .filter(
                HealthCheck.dog_id == dog_id,
                HealthCheck.date == data.date,
                HealthCheck.category == data.item,
            )
            .first()
        )
        if existing:
            raise ValueError("이미 해당 항목의 건강 기록이 존재합니다.")

        record = HealthCheck(
            dog_id=dog_id,
            date=data.date,
            category=data.item,
            is_normal=data.is_normal,
            memo=data.memo,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def create_walk_record(dog_id: int, data: WalkRecordCreate, db: Session):
        existing = (
            db.query(WalkRecord)
            .filter(WalkRecord.dog_id == dog_id, WalkRecord.date == data.date)
            .first()
        )
        if existing:
            raise ValueError("이미 해당 날짜의 산책 기록이 존재합니다.")

        record = WalkRecord(
            dog_id=dog_id,
            date=data.date,
            distance_km=data.distance_km,
            duration_min=data.duration_minutes,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def create_food_record(dog_id: int, data: FoodRecordCreate, db: Session):
        existing = (
            db.query(FoodRecord)
            .filter(
                FoodRecord.dog_id == dog_id,
                FoodRecord.date == data.date,
                FoodRecord.time == data.time,
            )
            .first()
        )
        if existing:
            raise ValueError("이미 해당 시간의 사료 기록이 존재합니다.")

        record = FoodRecord(
            dog_id=dog_id,
            date=data.date,
            time=data.time,
            brand=data.brand,
            amount_g=data.amount_g,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def create_water_record(dog_id: int, data: WaterRecordCreate, db: Session):
        existing = (
            db.query(WaterIntake)
            .filter(WaterIntake.dog_id == dog_id, WaterIntake.date == data.date)
            .first()
        )
        if existing:
            raise ValueError("이미 해당 날짜의 물 섭취 기록이 존재합니다.")

        record = WaterIntake(
            dog_id=dog_id,
            date=data.date,
            amount_ml=data.amount_ml,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def create_weight_record(dog_id: int, data: WeightRecordCreate, db: Session):
        existing = (
            db.query(WeightRecord)
            .filter(WeightRecord.dog_id == dog_id, WeightRecord.date == data.date)
            .first()
        )
        if existing:
            raise ValueError("이미 해당 날짜의 체중 기록이 존재합니다.")

        record = WeightRecord(
            dog_id=dog_id,
            date=data.date,
            weight_kg=data.weight_kg,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_weekly_report(dog_id: int, db: Session):
        today = datetime.now(tz=KST).date()
        week_start = today - timedelta(days=today.weekday() + 1)  # 가장 최근 일요일
        week_end = week_start + timedelta(days=6)

        weight = (
            db.query(WeightRecord.weight_kg)
            .filter(WeightRecord.dog_id == dog_id, WeightRecord.date <= week_end)
            .order_by(WeightRecord.date.desc())
            .first()
        )

        walk_records = (
            db.query(WalkRecord)
            .filter(
                WalkRecord.dog_id == dog_id,
                WalkRecord.date.between(week_start, week_end),
            )
            .all()
        )
        walk_count = len(walk_records)
        avg_walk_duration = (
            sum(r.duration_min for r in walk_records) / walk_count
            if walk_count
            else 0
        )

        health_check_count = (
            db.query(HealthCheck)
            .filter(
                HealthCheck.dog_id == dog_id,
                HealthCheck.date.between(week_start, week_end),
            )
            .count()
        )

        total_water = (
            db.query(func.sum(WaterIntake.amount_ml))
            .filter(
                WaterIntake.dog_id == dog_id,
                WaterIntake.date.between(week_start, week_end),
            )
            .scalar()
            or 0
        )

        total_food = (
            db.query(func.sum(FoodRecord.amount_g))
            .filter(
                FoodRecord.dog_id == dog_id,
                FoodRecord.date.between(week_start, week_end),
            )
            .scalar()
            or 0
        )

        return WeeklyReportResponse(
            week_start=week_start,
            week_end=week_end,
            current_weight=weight[0] if weight else None,
            avg_walk_duration=avg_walk_duration,
            walk_count=walk_count,
            health_check_count=health_check_count,
            total_water_ml=total_water,
            total_food_g=total_food,
        )

    # HealthDailyRecord CRUD
    @staticmethod
    def get_health_daily_record_by_id(record_id: int, db: Session):
        return (
            db.query(HealthCheck)
            .filter(HealthCheck.id == record_id)
            .first()
        )

    @staticmethod
    def update_health_daily_record(
        record_id: int, data: HealthDailyCreate, db: Session
    ):
        record = (
            db.query(HealthCheck)
            .filter(HealthCheck.id == record_id)
            .first()
        )
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        record.date = data.date
        record.category = data.item
        record.status = "정상" if data.is_normal else "이상"
        record.memo = data.memo
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_health_daily_record(record_id: int, db: Session):
        record = (
            db.query(HealthCheck)
            .filter(HealthCheck.id == record_id)
            .first()
        )
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        db.delete(record)
        db.commit()

    # WalkRecord CRUD
    @staticmethod
    def get_walk_record_by_id(record_id: int, db: Session):
        return db.query(WalkRecord).filter(WalkRecord.id == record_id).first()

    @staticmethod
    def update_walk_record(record_id: int, data: WalkRecordCreate, db: Session):
        record = db.query(WalkRecord).filter(WalkRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        record.date = data.date
        record.distance_km = data.distance_km
        record.duration_min = data.duration_minutes
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_walk_record(record_id: int, db: Session):
        record = db.query(WalkRecord).filter(WalkRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        db.delete(record)
        db.commit()

    # FoodRecord CRUD
    @staticmethod
    def get_food_record_by_id(record_id: int, db: Session):
        return db.query(FoodRecord).filter(FoodRecord.id == record_id).first()

    @staticmethod
    def update_food_record(record_id: int, data: FoodRecordCreate, db: Session):
        record = db.query(FoodRecord).filter(FoodRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        record.date = data.date
        record.time = data.time
        record.brand = data.brand
        record.amount_g = data.amount_g
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_food_record(record_id: int, db: Session):
        record = db.query(FoodRecord).filter(FoodRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        db.delete(record)
        db.commit()

    # WaterRecord CRUD
    @staticmethod
    def get_water_record_by_id(record_id: int, db: Session):
        return db.query(WaterIntake).filter(WaterIntake.id == record_id).first()

    @staticmethod
    def update_water_record(record_id: int, data: WaterRecordCreate, db: Session):
        record = db.query(WaterIntake).filter(WaterIntake.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        record.date = data.date
        record.amount_ml = data.amount_ml
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_water_record(record_id: int, db: Session):
        record = db.query(WaterIntake).filter(WaterIntake.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        db.delete(record)
        db.commit()

    # WeightRecord CRUD
    @staticmethod
    def get_weight_record_by_id(record_id: int, db: Session):
        return db.query(WeightRecord).filter(WeightRecord.id == record_id).first()

    @staticmethod
    def update_weight_record(record_id: int, data: WeightRecordCreate, db: Session):
        record = db.query(WeightRecord).filter(WeightRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        record.date = data.date
        record.weight_kg = data.weight_kg
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_weight_record(record_id: int, db: Session):
        record = db.query(WeightRecord).filter(WeightRecord.id == record_id).first()
        if not record:
            raise ValueError("기록을 찾을 수 없습니다.")
        db.delete(record)
        db.commit()

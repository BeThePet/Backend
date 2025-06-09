from db.models import VaccinationRecord, VaccineType
from sqlalchemy.orm import Session

from api.schemas.vaccine import VaccinationCreate


def list_vaccine_types(db: Session):
    return db.query(VaccineType).all()


def create_vaccination_record(dog_id: int, data: VaccinationCreate, db: Session):
    record = VaccinationRecord(
        dog_id=dog_id,
        vaccine_id=data.vaccine_id,
        date=data.date,
        hospital=data.hospital,
        memo=data.memo,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_vaccination_records(dog_id: int, db: Session):
    return db.query(VaccinationRecord).filter(VaccinationRecord.dog_id == dog_id).all()


def update_vaccination_record(
    vaccination_id: int, dog_id: int, data: VaccinationCreate, db: Session
):
    record = (
        db.query(VaccinationRecord)
        .filter(
            VaccinationRecord.id == vaccination_id, VaccinationRecord.dog_id == dog_id
        )
        .first()
    )

    if not record:
        raise ValueError("해당하는 백신 접종 기록을 찾을 수 없습니다.")

    # 업데이트할 데이터 적용
    for field, value in data.model_dump().items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


def delete_vaccination_record(vaccination_id: int, dog_id: int, db: Session):
    record = (
        db.query(VaccinationRecord)
        .filter(
            VaccinationRecord.id == vaccination_id, VaccinationRecord.dog_id == dog_id
        )
        .first()
    )
    if record:
        db.delete(record)
        db.commit()

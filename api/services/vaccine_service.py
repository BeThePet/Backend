from sqlalchemy.orm import Session
from db.models import VaccineType, VaccinationRecord
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
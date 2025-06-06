from db.models import Medication
from sqlalchemy.orm import Session

from api.schemas.medic import MedicationCreate


class MedicationService:
    @staticmethod
    def create_medication(dog_id: int, data: MedicationCreate, db: Session):
        medication = Medication(dog_id=dog_id, **data.model_dump())
        db.add(medication)
        db.commit()
        db.refresh(medication)
        return medication

    @staticmethod
    def list_medications(dog_id: int, db: Session):
        return db.query(Medication).filter(Medication.dog_id == dog_id).all()

    @staticmethod
    def delete_medication(medication_id: int, dog_id: int, db: Session):
        medication = (
            db.query(Medication)
            .filter(Medication.id == medication_id, Medication.dog_id == dog_id)
            .first()
        )
        if medication:
            db.delete(medication)
            db.commit()

    @staticmethod
    def update_medication(
        medication_id: int, dog_id: int, data: MedicationCreate, db: Session
    ):
        medication = (
            db.query(Medication)
            .filter(Medication.id == medication_id, Medication.dog_id == dog_id)
            .first()
        )

        if not medication:
            raise ValueError("해당하는 약 복용 정보를 찾을 수 없습니다.")

        # 업데이트할 데이터 적용
        for field, value in data.model_dump().items():
            setattr(medication, field, value)

        db.commit()
        db.refresh(medication)
        return medication

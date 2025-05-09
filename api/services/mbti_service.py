from db.models import DogMbti
from sqlalchemy.orm import Session


class MbtiService:
    @staticmethod
    def save_mbti_result(dog_id: int, mbti_type: str, db: Session):
        existing = db.query(DogMbti).filter(DogMbti.dog_id == dog_id).first()
        if existing:
            existing.mbti_type = mbti_type
        else:
            db.add(DogMbti(dog_id=dog_id, mbti_type=mbti_type))
        db.commit()

    @staticmethod
    def get_mbti_result(dog_id: int, db: Session):
        return db.query(DogMbti).filter(DogMbti.dog_id == dog_id).first()

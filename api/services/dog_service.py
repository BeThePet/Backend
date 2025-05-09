from core.security import get_current_user
from db.models import Allergy, Breed, Disease, Dog, DogAllergy, DogDisease
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.schemas.dog import DogCreate, DogResponse, DogUpdate


class DogService:
    @staticmethod
    def create_dog(user_id: int, dog_data: DogCreate, db: Session):
        if db.query(Dog).filter(Dog.user_id == user_id).first():
            raise HTTPException(
                status_code=400, detail="이미 반려견이 등록되어 있습니다"
            )

        if dog_data.breed_id is not None:
            breed = db.query(Breed).filter(Breed.id == dog_data.breed_id).first()
            if not breed:
                raise HTTPException(status_code=400, detail="존재하지 않는 품종입니다")

        valid_allergy_ids = set(
            a.id
            for a in db.query(Allergy)
            .filter(Allergy.id.in_(dog_data.allergy_ids))
            .all()
        )
        if len(valid_allergy_ids) != len(set(dog_data.allergy_ids)):
            raise HTTPException(
                status_code=400, detail="유효하지 않은 알러지 ID가 포함되어 있습니다"
            )

        valid_disease_ids = set(
            d.id
            for d in db.query(Disease)
            .filter(Disease.id.in_(dog_data.disease_ids))
            .all()
        )
        if len(valid_disease_ids) != len(set(dog_data.disease_ids)):
            raise HTTPException(
                status_code=400, detail="유효하지 않은 질병 ID가 포함되어 있습니다"
            )

        dog = Dog(
            name=dog_data.name,
            birth_date=dog_data.birth_date,
            age_group=dog_data.age_group,
            weight=dog_data.weight,
            breed_id=dog_data.breed_id,
            gender=dog_data.gender,
            current_medication=dog_data.medication,
            user_id=user_id,
        )
        db.add(dog)
        db.commit()
        db.refresh(dog)

        for allergy_id in dog_data.allergy_ids:
            db.add(DogAllergy(dog_id=dog.id, allergy_id=allergy_id))
        for disease_id in dog_data.disease_ids:
            db.add(DogDisease(dog_id=dog.id, disease_id=disease_id))

        db.commit()
        return dog

    @staticmethod
    def update_dog(user_id: int, dog_data: DogUpdate, db: Session):
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        if dog_data.breed_id is not None:
            breed = db.query(Breed).filter(Breed.id == dog_data.breed_id).first()
            if not breed:
                raise HTTPException(status_code=400, detail="존재하지 않는 품종입니다")

        valid_allergy_ids = set(
            a.id
            for a in db.query(Allergy)
            .filter(Allergy.id.in_(dog_data.allergy_ids))
            .all()
        )
        if len(valid_allergy_ids) != len(set(dog_data.allergy_ids)):
            raise HTTPException(
                status_code=400, detail="유효하지 않은 알러지 ID가 포함되어 있습니다"
            )

        valid_disease_ids = set(
            d.id
            for d in db.query(Disease)
            .filter(Disease.id.in_(dog_data.disease_ids))
            .all()
        )
        if len(valid_disease_ids) != len(set(dog_data.disease_ids)):
            raise HTTPException(
                status_code=400, detail="유효하지 않은 질병 ID가 포함되어 있습니다"
            )

        dog.name = dog_data.name or dog.name
        dog.birth_date = dog_data.birth_date or dog.birth_date
        dog.age_group = dog_data.age_group or dog.age_group
        dog.weight = dog_data.weight or dog.weight
        dog.breed_id = dog_data.breed_id or dog.breed_id
        dog.gender = dog_data.gender or dog.gender
        dog.current_medication = dog_data.medication or dog.current_medication

        db.commit()
        db.refresh(dog)

        db.query(DogAllergy).filter(DogAllergy.dog_id == dog.id).delete()
        db.query(DogDisease).filter(DogDisease.dog_id == dog.id).delete()
        db.commit()

        for allergy_id in dog_data.allergy_ids:
            db.add(DogAllergy(dog_id=dog.id, allergy_id=allergy_id))
        for disease_id in dog_data.disease_ids:
            db.add(DogDisease(dog_id=dog.id, disease_id=disease_id))
        db.commit()

        return dog

    @staticmethod
    def to_response(dog: Dog) -> DogResponse:
        return DogResponse(
            id=dog.id,
            name=dog.name,
            birth_date=dog.birth_date,
            age_group=dog.age_group,
            weight=dog.weight,
            gender=dog.gender,
            medication=dog.current_medication,
            breed_name=dog.breed.name if dog.breed else None,
            allergy_names=[da.allergy.name for da in dog.allergies],
            disease_names=[dd.disease.name for dd in dog.diseases],
        )

    @staticmethod
    def delete_dog(user_id: int, db: Session):
        dog = db.query(Dog).filter(Dog.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="등록된 반려견이 없습니다.")

        
        db.query(DogAllergy).filter(DogAllergy.dog_id == dog.id).delete()
        db.query(DogDisease).filter(DogDisease.dog_id == dog.id).delete()

        
        db.delete(dog)
        db.commit()
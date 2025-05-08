from db.models import Allergy, AllergyCategory, Breed, Disease, DiseaseCategory
from sqlalchemy.orm import Session


class OptionService:
    @staticmethod
    def get_breeds(db: Session):
        breeds = db.query(Breed).all()
        return [{"id": b.id, "name": b.name} for b in breeds]

    @staticmethod
    def get_allergy_categories(db: Session):
        categories = db.query(AllergyCategory).all()
        result = []
        for cat in categories:
            items = db.query(Allergy).filter(Allergy.category_id == cat.id).all()
            result.append(
                {
                    "category": cat.name,
                    "items": [{"id": a.id, "name": a.name} for a in items],
                }
            )
        return result

    @staticmethod
    def get_disease_categories(db: Session):
        categories = db.query(DiseaseCategory).all()
        result = []
        for cat in categories:
            items = db.query(Disease).filter(Disease.category_id == cat.id).all()
            result.append(
                {
                    "category": cat.name,
                    "items": [{"id": d.id, "name": d.name} for d in items],
                }
            )
        return result

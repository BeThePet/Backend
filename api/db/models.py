from core.base import TimeStampMixin
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .base import Base


class User(Base, TimeStampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), unique=True, nullable=False)

    dogs = relationship("Dog", back_populates="owner")


class Dog(Base, TimeStampMixin):
    __tablename__ = "dogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    age_group = Column(String(20), nullable=False)  # 주니어, 성견, 시니어
    weight = Column(Float, nullable=False)
    gender = Column(String(10), nullable=False)  # 남아, 여아, 중성화
    current_medication = Column(String(255), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    breed_id = Column(Integer, ForeignKey("breeds.id"), nullable=False)

    owner = relationship("User", back_populates="dogs")
    breed = relationship("Breed")
    allergies = relationship("DogAllergy", back_populates="dog")
    diseases = relationship("DogDisease", back_populates="dog")


class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class AllergyCategory(Base):
    __tablename__ = "allergy_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    allergies = relationship("Allergy", back_populates="category")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("allergy_categories.id"))

    category = relationship("AllergyCategory", back_populates="allergies")
    synonyms = relationship("AllergySynonym", back_populates="allergy")


class AllergySynonym(Base):
    __tablename__ = "allergy_synonyms"

    id = Column(Integer, primary_key=True)
    allergy_id = Column(Integer, ForeignKey("allergies.id"), nullable=False)
    synonym = Column(String(100), nullable=False)

    allergy = relationship("Allergy", back_populates="synonyms")


class Disease(Base):
    __tablename__ = "diseases"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("disease_categories.id"))

    category = relationship("DiseaseCategory", back_populates="diseases")


class DiseaseCategory(Base):
    __tablename__ = "disease_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    diseases = relationship("Disease", back_populates="category")


class DogAllergy(Base):
    __tablename__ = "dog_allergies"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    allergy_id = Column(Integer, ForeignKey("allergies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dog = relationship("Dog", back_populates="allergies")
    allergy = relationship("Allergy")


class DogDisease(Base):
    __tablename__ = "dog_diseases"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dog = relationship("Dog", back_populates="diseases")
    disease = relationship("Disease")

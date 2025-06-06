import uuid
from datetime import datetime

from db.enums import HealthStatus, HospitalType, Specialty
from sqlalchemy import ARRAY, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.base import TimeStampMixin

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
    age_group = Column(String(20), nullable=False)
    weight = Column(Float, nullable=False)
    gender = Column(String(10), nullable=False)
    current_medication = Column(String(255), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    breed_id = Column(Integer, ForeignKey("breeds.id"), nullable=False)

    owner = relationship("User", back_populates="dogs")
    breed = relationship("Breed")
    allergies = relationship("DogAllergy", back_populates="dog")
    diseases = relationship("DogDisease", back_populates="dog")
    mbti = relationship("DogMbti", back_populates="dog", uselist=False)
    health_checks = relationship("HealthCheck", back_populates="dog")
    walk_records = relationship("WalkRecord", back_populates="dog")
    food_records = relationship("FoodRecord", back_populates="dog")
    water_intakes = relationship("WaterIntake", back_populates="dog")
    weight_records = relationship("WeightRecord", back_populates="dog")
    medications = relationship("Medication", back_populates="dog")
    vaccinations = relationship("VaccinationRecord", back_populates="dog")


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


class DogAllergy(Base, TimeStampMixin):
    __tablename__ = "dog_allergies"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    allergy_id = Column(Integer, ForeignKey("allergies.id"), nullable=False)

    dog = relationship("Dog", back_populates="allergies")
    allergy = relationship("Allergy")


class DogDisease(Base, TimeStampMixin):
    __tablename__ = "dog_diseases"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)

    dog = relationship("Dog", back_populates="diseases")
    disease = relationship("Disease")


class DogMbti(Base, TimeStampMixin):
    __tablename__ = "dog_mbtis"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False, unique=True)
    mbti_type = Column(String(4), nullable=False)

    dog = relationship("Dog", back_populates="mbti")


class HealthCheck(Base, TimeStampMixin):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    category = Column(
        String(20), nullable=False
    )  # e.g., appetite, vitality, hydration, etc.
    status = Column(SQLAlchemyEnum(HealthStatus, name="healthstatus"), nullable=False)
    memo = Column(String(255), nullable=True)

    dog = relationship("Dog", back_populates="health_checks")


class WalkRecord(Base, TimeStampMixin):
    __tablename__ = "walk_records"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_min = Column(Integer, nullable=False)

    dog = relationship("Dog", back_populates="walk_records")


class FoodRecord(Base, TimeStampMixin):
    __tablename__ = "food_records"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    time = Column(Time, nullable=False)
    brand = Column(String(100), nullable=True)
    amount_g = Column(Integer, nullable=False)

    dog = relationship("Dog", back_populates="food_records")


class WaterIntake(Base, TimeStampMixin):
    __tablename__ = "water_intakes"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    amount_ml = Column(Integer, nullable=False)

    dog = relationship("Dog", back_populates="water_intakes")


class WeightRecord(Base, TimeStampMixin):
    __tablename__ = "weight_records"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)

    dog = relationship("Dog", back_populates="weight_records")


class Medication(Base, TimeStampMixin):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 약 이름
    time = Column(Time, nullable=False)  # 복용 시간
    weekdays = Column(String(20), nullable=False)
    dosage = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    memo = Column(String(255), nullable=True)
    alarm_enabled = Column(Boolean, default=False)

    dog = relationship("Dog", back_populates="medications")


class VaccineCategory(str):
    REQUIRED = "필수"
    OPTIONAL = "선택"


class VaccineType(Base):
    __tablename__ = "vaccine_types"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(10), nullable=False)
    description = Column(String(255), nullable=True)
    period = Column(Integer, nullable=False)  # 예방주기(일 단위)

    vaccinations = relationship("VaccinationRecord", back_populates="vaccine")


class VaccinationRecord(Base, TimeStampMixin):
    __tablename__ = "vaccination_records"

    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    vaccine_id = Column(String, ForeignKey("vaccine_types.id"), nullable=False)
    date = Column(Date, nullable=False)
    hospital = Column(String(100), nullable=True)
    memo = Column(String(255), nullable=True)

    vaccine = relationship("VaccineType", back_populates="vaccinations")
    dog = relationship("Dog", back_populates="vaccinations")


class Hospital(Base, TimeStampMixin):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    address = Column(String(255), nullable=True)
    type = Column(SQLAlchemyEnum(HospitalType, name="hospital_type"), nullable=False)
    is_emergency = Column(Boolean, default=False)
    hours = Column(String(100), nullable=True)
    notes = Column(String(255), nullable=True)
    specialties = Column(ARRAY(SQLAlchemyEnum(Specialty, name="specialty_enum")))


class EmergencyGuide(Base, TimeStampMixin):
    __tablename__ = "emergency_guides"

    id = Column(String, primary_key=True)  # "poisoning", "fracture" 등
    title = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # high / medium / low
    symptoms = Column(ARRAY(String), nullable=False)
    first_aid = Column(ARRAY(String), nullable=False)
    notes = Column(String(1000), nullable=True)


# 챗봇 관련 모델 추가
class ChatRoom(Base, TimeStampMixin):
    __tablename__ = "chat_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255))

    # Relationships
    messages = relationship(
        "ChatMessage", back_populates="chat_room", cascade="all, delete-orphan"
    )
    symptom_logs = relationship(
        "SymptomLog", back_populates="chat_room", cascade="all, delete-orphan"
    )
    user = relationship("User", backref="chat_rooms")


class ChatMessage(Base, TimeStampMixin):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    user = relationship("User", backref="chat_messages")


class NewSymptom(Base, TimeStampMixin):
    __tablename__ = "new_symptoms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symptom_name = Column(String(255), nullable=False, unique=True)
    normalized_name = Column(String(255))
    category = Column(String(100))
    severity = Column(Integer)
    description = Column(Text)
    related_symptoms = Column(ARRAY(String))
    possible_causes = Column(ARRAY(String))


class SymptomLog(Base, TimeStampMixin):
    __tablename__ = "symptom_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_room_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptom_name = Column(String(255), nullable=False)
    context = Column(Text)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="symptom_logs")
    user = relationship("User", backref="symptom_logs")

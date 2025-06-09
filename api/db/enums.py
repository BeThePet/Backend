import enum


class HealthStatus(str, enum.Enum):
    normal = "정상"
    warning = "주의"
    abnormal = "이상"


class HospitalType(str, enum.Enum):
    REGULAR = "일반 병원"
    EMERGENCY = "응급 병원"
    SPECIALIST = "전문 병원"


class Specialty(str, enum.Enum):
    GENERAL = "일반 진료"
    EMERGENCY = "응급 처치"
    SURGERY = "외과"
    INTERNAL = "내과"
    DERMATOLOGY = "피부과"
    OPHTHALMOLOGY = "안과"
    DENTISTRY = "치과"
    ICU = "중환자실"
    EXOTIC = "특수동물"

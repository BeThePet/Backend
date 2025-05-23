import enum

class HealthStatus(str, enum.Enum):
    normal = "정상"
    warning = "주의"
    abnormal = "이상"
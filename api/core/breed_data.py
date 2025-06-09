# /api/db/scripts/seed_data/breeds.csv 에 있는 품종 ID 기준
# 실제 서비스에서는 모든 품종에 대해 분류가 필요합니다.

# 소형견 (체중 ~10kg)
SMALL_BREED_IDS = {
    1,  # 말티즈
    2,  # 푸들
    3,  # 포메라니안
    4,  # 치와와
    5,  # 요크셔테리어
    6,  # 시츄
    7,  # 닥스훈트
    9,  # 비숑 프리제
    10,  # 퍼그
    13,  # 미니어처 핀셔
    14,  # 빠삐용
    15,  # 이탈리안 그레이하운드
    18,  # 재패니즈 스피츠
    21,  # 페키니즈
    32,  # 스코티시 테리어
}

# 대형견 (체중 ~25kg 이상)
LARGE_BREED_IDS = {
    8,  # 골든 리트리버
    11,  # 래브라도 리트리버
    12,  # 시베리안 허스키
    16,  # 저먼 셰퍼드
    17,  # 도베르만 핀셔
    19,  # 사모예드
    20,  # 보더 콜리
    22,  # 스탠더드 푸들
    23,  # 알래스칸 맬러뮤트
    25,  # 그레이트 데인
    26,  # 버니즈 마운틴 도그
    28,  # 복서
    31,  # 로트와일러
    39,  # 올드 잉글리시 십독
    44,  # 와이마라너
}


def get_breed_size_group(breed_id: int) -> str:
    """품종 ID를 기반으로 크기 그룹을 반환"""
    if breed_id in SMALL_BREED_IDS:
        return "small"
    if breed_id in LARGE_BREED_IDS:
        return "large"
    return "medium"

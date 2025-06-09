# 한글 질병명 -> 영문 질병명 매핑
# seed_data.py의 질병들을 disease_avoid.csv의 질병들로 매핑

DISEASE_KO_TO_EN = {
    # 소화기 질환
    "위염": "Gastrointestinal Issues",
    "췌장염": "Pancreatitis",
    "염증성 장질환": "IBD (Inflammatory Bowel Disease)",
    "대장염": "IBD (Inflammatory Bowel Disease)",
    "위 확장": "Gastrointestinal Issues",
    "위 염전": "Gastrointestinal Issues",
    "거대식도증": "Gastrointestinal Issues",
    "간 질환": "Liver Disease",
    "담낭 질환": "Liver Disease",
    "변비": "Gastrointestinal Issues",
    "설사": "Gastrointestinal Issues",
    # 피부 질환
    "아토피 피부염": "Skin Conditions",
    "벼룩 알레르기": "Allergic Dermatitis",
    "핫스팟": "Skin Conditions",
    "효모 감염": "Skin Conditions",
    "백선": "Skin Conditions",
    "개선충증": "Skin Conditions",
    "지루성 피부염": "Skin Conditions",
    "핥는 육아종": "Skin Conditions",
    "농피증": "Skin Conditions",
    "탈모": "Skin Conditions",
    "피부 종양": "Cancer",
    # 관절 및 뼈 질환
    "관절염": "Joint Disease",
    "고관절 이형성증": "Joint Disease",
    "십자인대 손상": "Joint Disease",
    "골관절염": "Joint Disease",
    "팔꿈치 이형성증": "Joint Disease",
    "슬개골 탈구": "Joint Disease",
    "골연골증": "Joint Disease",
    "추간판 질환": "Joint Disease",
    "워블러 증후군": "Joint Disease",
    "비대성 골이영양증": "Joint Disease",
    # 심장 및 호흡기 질환
    "심장 잡음": "Heart Disease",
    "울혈성 심부전": "Heart Disease",
    "확장성 심근병증": "Heart Disease",
    "승모판 질환": "Heart Disease",
    "심장사상충": "Heart Disease",
    "기관지염": "Heart Disease",
    "폐렴": "Heart Disease",
    "켄넬코프": "Heart Disease",
    "기관 허탈": "Heart Disease",
    "폐부종": "Heart Disease",
    # 신경 및 면역계 질환
    "간질": "Epilepsy",
    "전정기관 질환": "Epilepsy",
    "수막염": "Epilepsy",
    "뇌염": "Epilepsy",
    "자가면역 질환": "Food Allergies",
    "루푸스": "Food Allergies",
    "중증근무력증": "Food Allergies",
    "갑상선 기능저하증": "Hypothyroidism",
    "갑상선 기능항진증": "Hypothyroidism",
    "쿠싱병": "Cushing's Disease",
    "애디슨병": "Hypothyroidism",
    # 눈 및 귀 질환 (추천모듈에 직접 대응되는 질병 없음)
    "백내장": None,
    "녹내장": None,
    "결막염": None,
    "진행성 망막위축": None,
    "체리아이": None,
    "귀 감염": None,
    "귀진드기": None,
    "청각 장애": None,
    "외이염": None,
    # 비뇨기 및 생식기 질환
    "요로 감염": "Urinary Stones",
    "신장 질환": "Kidney Disease",
    "방광 결석": "Urinary Stones",
    "요실금": "Urinary Stones",
    "전립선 문제": "Urinary Stones",
    "자궁축농증": None,
    "유선 종양": "Cancer",
    "고환 종양": "Cancer",
    "잠복고환": None,
    # 기타 질환
    "당뇨병": "Diabetes",
    "비만": "Obesity",
    "암": "Cancer",
    "빈혈": "Anemia",
    "치과 질환": "Dental Disease",
    "기생충": None,
    "라임병": None,
    "파보바이러스": None,
    "디스템퍼": None,
    "렙토스피라증": None,
}


def map_diseases_ko_to_en(korean_diseases: list) -> list:
    """한글 질병명 리스트를 영문 질병명 리스트로 변환"""
    english_diseases = []
    for ko_disease in korean_diseases:
        en_disease = DISEASE_KO_TO_EN.get(ko_disease)
        if en_disease:  # None이 아닌 경우만 추가
            english_diseases.append(en_disease)

    # 중복 제거
    return list(set(english_diseases))

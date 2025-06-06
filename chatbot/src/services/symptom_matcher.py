import json
from pathlib import Path
from typing import List, Tuple

# Load JSON 데이터
BASE_DIR = Path(__file__).parent.parent  # services의 상위 디렉토리인 src로 변경
DATA_DIR = BASE_DIR / "data"
STATIC_DATA_DIR = DATA_DIR / "static"

# 파일 경로 설정
SYMPTOM_MAP_FILE = STATIC_DATA_DIR / "symptom_synonyms_updated.json"
DISEASE_MAP_FILE = STATIC_DATA_DIR / "disease_symptom_map.json"

# Load JSON 데이터
with open(SYMPTOM_MAP_FILE, encoding="utf-8") as f:
    SYMPTOM_MAP = json.load(f)

with open(DISEASE_MAP_FILE, encoding="utf-8") as f:
    DISEASE_MAP = json.load(f)

# 역매핑: 동의어 → 대표 증상
SYNONYM_TO_SYMPTOM = {}
for rep_symptom, synonyms in SYMPTOM_MAP.items():
    SYNONYM_TO_SYMPTOM[rep_symptom] = rep_symptom
    for synonym in synonyms:
        SYNONYM_TO_SYMPTOM[synonym] = rep_symptom


def normalize_symptoms(symptoms: List[str]) -> List[str]:
    """입력된 증상 리스트를 대표 증상명으로 정규화"""
    normalized = []
    for s in symptoms:
        normalized.append(SYNONYM_TO_SYMPTOM.get(s.strip(), s.strip()))
    return normalized


def match_diseases(user_symptoms: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
    """
    사용자 입력 증상 → 질병 추천 Top-K
    :param user_symptoms: 사용자 입력 증상 리스트 (ex: ["구토", "배탈"])
    :param top_k: 추천할 질병 수
    :return: (질병명, 점수) 리스트
    """
    normalized_input = normalize_symptoms(user_symptoms)
    results = []

    for disease, disease_symptoms in DISEASE_MAP.items():
        disease_set = set(disease_symptoms)
        input_set = set(normalized_input)

        matched = input_set & disease_set
        score = len(matched) / len(disease_set) if disease_set else 0
        if score > 0:
            results.append((disease, round(score, 3)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


# 테스트용 예시
if __name__ == "__main__":
    example_input = ["구토", "무기력", "배탈"]
    predictions = match_diseases(example_input)
    for disease, score in predictions:
        print(f"❗ 의심 질병: {disease} ({score * 100:.1f}%)")

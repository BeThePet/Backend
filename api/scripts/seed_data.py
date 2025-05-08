from db.models import Allergy, AllergyCategory, Breed, Disease, DiseaseCategory
from db.session import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

breeds = [
    "말티즈",
    "푸들",
    "포메라이언",
    "시츄",
    "웰시코기",
    "치와와",
    "비숑프리제",
    "요크셔테리어",
    "프렌치 불독",
    "골든리트리버",
    "보더콜리",
    "비글",
    "닥스훈트",
    "시바이누",
    "진돗개",
    "믹스견",
    "기타",
]

allergyCategories = [
    {
        "name": "단백질 및 육류",
        "items": [
            "닭고기",
            "소고기",
            "돼지고기",
            "양고기",
            "칠면조",
            "오리고기",
            "토끼고기",
            "사슴고기",
            "캥거루고기",
            "메추라기",
        ],
    },
    {
        "name": "해산물",
        "items": [
            "연어",
            "참치",
            "흰살생선",
            "조개류",
            "새우",
            "게",
            "오징어",
            "멸치",
            "고등어",
            "정어리",
        ],
    },
    {
        "name": "곡물",
        "items": [
            "밀",
            "옥수수",
            "대두",
            "쌀",
            "보리",
            "귀리",
            "호밀",
            "퀴노아",
            "기장",
            "메밀",
        ],
    },
    {
        "name": "유제품",
        "items": [
            "우유",
            "치즈",
            "요거트",
            "버터",
            "크림",
            "아이스크림",
            "유청",
            "카제인",
        ],
    },
    {
        "name": "견과류 및 씨앗",
        "items": [
            "땅콩",
            "아몬드",
            "호두",
            "캐슈넛",
            "피스타치오",
            "아마씨",
            "참깨",
            "해바라기씨",
            "호박씨",
        ],
    },
    {
        "name": "과일 및 채소",
        "items": [
            "사과",
            "바나나",
            "당근",
            "감자",
            "토마토",
            "아보카도",
            "브로콜리",
            "시금치",
            "완두콩",
            "고구마",
        ],
    },
    {
        "name": "첨가물",
        "items": [
            "인공색소",
            "인공향료",
            "방부제",
            "BHA/BHT",
            "프로필렌 글리콜",
            "에톡시퀸",
            "MSG",
            "아황산염",
            "질산염",
        ],
    },
]

diseaseCategories = [
    {
        "name": "소화기 질환",
        "items": [
            "위염",
            "췌장염",
            "염증성 장질환",
            "대장염",
            "위 확장",
            "위 염전",
            "거대식도증",
            "간 질환",
            "담낭 질환",
            "변비",
            "설사",
        ],
    },
    {
        "name": "피부 질환",
        "items": [
            "아토피 피부염",
            "벼룩 알레르기",
            "핫스팟",
            "효모 감염",
            "백선",
            "개선충증",
            "지루성 피부염",
            "핥는 육아종",
            "농피증",
            "탈모",
            "피부 종양",
        ],
    },
    {
        "name": "관절 및 뼈 질환",
        "items": [
            "관절염",
            "고관절 이형성증",
            "십자인대 손상",
            "골관절염",
            "팔꿈치 이형성증",
            "슬개골 탈구",
            "골연골증",
            "추간판 질환",
            "워블러 증후군",
            "비대성 골이영양증",
        ],
    },
    {
        "name": "심장 및 호흡기 질환",
        "items": [
            "심장 잡음",
            "울혈성 심부전",
            "확장성 심근병증",
            "승모판 질환",
            "심장사상충",
            "기관지염",
            "폐렴",
            "켄넬코프",
            "기관 허탈",
            "폐부종",
        ],
    },
    {
        "name": "신경 및 면역계 질환",
        "items": [
            "간질",
            "전정기관 질환",
            "수막염",
            "뇌염",
            "자가면역 질환",
            "루푸스",
            "중증근무력증",
            "갑상선 기능저하증",
            "갑상선 기능항진증",
            "쿠싱병",
            "애디슨병",
        ],
    },
    {
        "name": "눈 및 귀 질환",
        "items": [
            "백내장",
            "녹내장",
            "결막염",
            "진행성 망막위축",
            "체리아이",
            "귀 감염",
            "귀진드기",
            "청각 장애",
            "외이염",
        ],
    },
    {
        "name": "비뇨기 및 생식기 질환",
        "items": [
            "요로 감염",
            "신장 질환",
            "방광 결석",
            "요실금",
            "전립선 문제",
            "자궁축농증",
            "유선 종양",
            "고환 종양",
            "잠복고환",
        ],
    },
    {
        "name": "기타 질환",
        "items": [
            "당뇨병",
            "비만",
            "암",
            "빈혈",
            "치과 질환",
            "기생충",
            "라임병",
            "파보바이러스",
            "디스템퍼",
            "렙토스피라증",
        ],
    },
]


def seed_breeds(db: Session):
    try:
        for name in breeds:
            if not db.query(Breed).filter_by(name=name).first():
                db.add(Breed(name=name))
        db.commit()
        print("Breed 데이터 삽입 완료")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Breed 삽입 실패: {e}")


def seed_allergies(db: Session):
    try:
        for cat in allergyCategories:
            category = AllergyCategory(name=cat["name"])
            db.add(category)
            db.commit()
            for item in cat["items"]:
                db.add(Allergy(name=item, category_id=category.id))
        db.commit()
        print("Allergy 데이터 삽입 완료")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Allergy 삽입 실패: {e}")


def seed_diseases(db: Session):
    try:
        for cat in diseaseCategories:
            category = DiseaseCategory(name=cat["name"])
            db.add(category)
            db.commit()
            for item in cat["items"]:
                db.add(Disease(name=item, category_id=category.id))
        db.commit()
        print("Disease 데이터 삽입 완료")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Disease 삽입 실패: {e}")


if __name__ == "__main__":
    print("시드 데이터 삽입 시작")
    db = SessionLocal()
    seed_breeds(db)
    seed_allergies(db)
    seed_diseases(db)
    print("시드 데이터 삽입 완료")

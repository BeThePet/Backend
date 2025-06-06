import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session, joinedload

from api.db.models import (
    AllergyCategory,
    ChatMessage,
    ChatRoom,
    DiseaseCategory,
    Dog,
    NewSymptom,
    SymptomLog,
)

from ..schemas.chat import (
    ChatHistoryResponse,
    ChatMessageCreate,
    ChatRoomCreate,
    ChatRoomResponse,
    SymptomLogCreate,
)
from .symptom_matcher import match_diseases, normalize_symptoms


def check_required_env_vars():
    required_vars = ["OPENAI_API_KEY", "DB_HOST", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


# 시작시 환경변수 체크
check_required_env_vars()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 결과 캐싱을 위한 딕셔너리
symptom_cache = {}

# 파일 경로 설정
BASE_DIR = Path(__file__).parent.parent  # services의 상위 디렉토리인 src로 변경
DATA_DIR = BASE_DIR / "data"
STATIC_DATA_DIR = DATA_DIR / "static"
DYNAMIC_DATA_DIR = DATA_DIR / "dynamic"
LOG_DIR = DYNAMIC_DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 새로 발견된 증상들을 저장할 파일
NEW_SYMPTOMS_FILE = DYNAMIC_DATA_DIR / "new_symptoms.json"
SYMPTOMS_LOG_FILE = LOG_DIR / "symptoms_log.json"
DISEASE_DESCRIPTIONS_FILE = STATIC_DATA_DIR / "disease_descriptions.json"

# Static 파일 로드
current_dir = Path(__file__).parent.parent
with open(current_dir / "static" / "disease_map.json", "r", encoding="utf-8") as f:
    DISEASE_MAP = json.load(f)
with open(current_dir / "static" / "allergy_map.json", "r", encoding="utf-8") as f:
    ALLERGY_MAP = json.load(f)


# 질병 설명 DB 로드
def load_disease_descriptions():
    """질병 설명 데이터베이스 로드"""
    try:
        with open(DISEASE_DESCRIPTIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "위장염": "위와 장에 염증이 생긴 상태로, 구토, 설사, 복통 등의 증상을 보입니다.",
            "감기": "바이러스나 세균 감염으로 인한 상부 호흡기 질환입니다.",
            "알레르기": "특정 물질에 대한 과민반응으로 가려움, 발진 등의 증상을 보입니다.",
        }


DISEASE_DESCRIPTIONS = load_disease_descriptions()


def load_new_symptoms() -> Dict[str, Dict]:
    """새로 발견된 증상 데이터베이스 로드"""
    try:
        with open(NEW_SYMPTOMS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "symptoms": {},  # 증상 데이터
            "metadata": {  # 메타데이터
                "last_updated": datetime.now().isoformat(),
                "total_count": 0,
            },
        }


def save_new_symptoms(data: Dict):
    """새로 발견된 증상 저장"""
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    with open(NEW_SYMPTOMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_symptom_occurrence(symptom: str, context: str):
    """증상 발생 로깅"""
    try:
        with open(SYMPTOMS_LOG_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)
    except FileNotFoundError:
        log = []

    log.append(
        {
            "timestamp": datetime.now().isoformat(),
            "symptom": symptom,
            "context": context,
        }
    )

    with open(SYMPTOMS_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def analyze_new_symptom(symptom: str, context: str) -> Dict:
    """
    새로운 증상 분석
    """
    prompt = f"""
당신은 수의학 전문가입니다. 다음 증상을 분석해주세요:

증상: {symptom}
컨텍스트: {context}

다음 형식으로 JSON 응답을 생성해주세요:
{{
    "is_valid_symptom": true/false,  # 실제 증상인지 여부
    "normalized_name": "표준화된 증상명",
    "category": "행동/신체/정신 등 카테고리",
    "severity": 1-5,  # 심각도 (1: 매우 낮음, 5: 매우 높음)
    "description": "증상에 대한 간단한 설명",
    "related_symptoms": ["연관 증상1", "연관 증상2"],
    "possible_causes": ["가능한 원인1", "가능한 원인2"]
}}

응답은 반드시 유효한 JSON 형식이어야 합니다.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        result = response.choices[0].message.content
        return json.loads(result)

    except Exception as e:
        print(f"새로운 증상 분석 중 오류 발생: {e}")
        return {
            "is_valid_symptom": False,
            "normalized_name": symptom,
            "category": "unknown",
            "severity": 1,
            "description": "분석 실패",
            "related_symptoms": [],
            "possible_causes": [],
        }


def extract_symptoms_with_gpt(user_input: str) -> Tuple[List[str], List[str]]:
    """
    1단계: GPT-4로 자연어 질문에서 증상 추출 (새로운 증상도 포함)
    반환값: (known_symptoms, new_symptoms)
    """
    prompt = f"""
너는 수의학 전문가야. 보호자의 말에서 반려동물의 모든 증상을 추출해줘.

보호자 말: "{user_input}"

다음 형식으로 JSON 응답을 생성해줘:
{{
    "known_symptoms": ["기존 증상1", "기존 증상2"],  # 일반적으로 알려진 증상
    "new_symptoms": ["새로운 증상1", "새로운 증상2"]  # 특이하거나 새로운 증상/행동
}}

규칙:
1. known_symptoms는 다음 표준 용어를 사용:
   - 구토, 설사, 식욕부진, 무기력, 발열, 기침, 재채기
   - 가려움, 발진, 탈모, 호흡곤란, 복통, 설사
   - 혈뇨, 빈뇨, 눈물과다, 분비물, 악취

2. new_symptoms는 위 목록에 없지만 의미있는 증상이나 행동 변화

응답은 반드시 유효한 JSON 형식이어야 합니다.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )

        result_content = response.choices[0].message.content
        # LLM 응답이 JSON 형식이 아닐 경우를 대비한 예외 처리 추가
        try:
            result = json.loads(result_content)
        except json.JSONDecodeError:
            print(f"GPT 증상 추출 결과가 JSON 형식이 아닙니다: {result_content}")
            # Fallback:쉼표로 구분된 문자열로 간주하고 파싱 시도 (정규화 필요)
            # 이 부분은 실제 운영시 더 견고하게 만들어야 함
            if (
                "known_symptoms" in result_content.lower()
                or "new_symptoms" in result_content.lower()
            ):  # 간단한 체크
                print(
                    "Warning: GPT output not strict JSON, attempting loose parse for symptoms."
                )  # 임시 처리
                # 실제로는 여기서 에러 처리 또는 다른 방식으로 증상 추출을 시도해야 합니다.
                # 지금은 빈 리스트 반환
                return [], []
            else:  # 일반 문자열 응답이면, known_symptoms로 간주
                raw_symptoms = [
                    s.strip() for s in result_content.split(",") if s.strip()
                ]
                return normalize_symptoms(raw_symptoms), []

        known_symptoms = normalize_symptoms(result.get("known_symptoms", []))
        new_symptoms = result.get("new_symptoms", [])

        # 새로운 증상 분석 및 저장
        if new_symptoms:
            new_symptoms_db = load_new_symptoms()
            for symptom in new_symptoms:
                if symptom not in new_symptoms_db["symptoms"]:
                    analysis = analyze_new_symptom(symptom, user_input)
                    if analysis["is_valid_symptom"]:
                        new_symptoms_db["symptoms"][symptom] = analysis
                        new_symptoms_db["metadata"]["total_count"] += 1
                log_symptom_occurrence(symptom, user_input)
            save_new_symptoms(new_symptoms_db)

        return known_symptoms, new_symptoms

    except Exception as e:
        print(f"GPT 증상 추출 오류 (Outer): {e}")
        return [], []


def ask_for_additional_symptoms(
    initial_known: List[str], initial_new: List[str]
) -> Tuple[List[str], List[str]]:
    """
    2단계: 추가 증상 문의 (새로운 증상 지원)
    """
    if initial_known or initial_new:
        if initial_known:
            print(f"\n🔍 **파악된 일반 증상:** {', '.join(initial_known)}")
        if initial_new:
            print(f"🔍 **파악된 특이 증상/행동:** {', '.join(initial_new)}")
    else:
        print(f"\n🔍 **현재까지 명확한 증상이 파악되지 않았습니다.**")

    print("\n💬 **추가 증상이나 상태가 있나요?**")
    print("   예: 열이 있어요, 기침을 해요, 설사를 해요 등")
    print("   특이한 행동이나 상태 변화도 알려주세요!")
    print("   (없으면 '없음' 또는 'no' 입력)")

    additional_input = input("➤ ").strip()

    if additional_input.lower() in ["없음", "no", "없어요", "없다", ""]:
        return initial_known, initial_new

    # 추가 증상도 GPT로 추출
    additional_known, additional_new = extract_symptoms_with_gpt(additional_input)

    if additional_known or additional_new:
        if additional_known:
            print(f"🔍 **추가 일반 증상:** {', '.join(additional_known)}")
        if additional_new:
            print(f"🔍 **추가 특이 증상/행동:** {', '.join(additional_new)}")

        # 중복 제거하면서 합치기
        all_known = list(set(initial_known + additional_known))
        all_new = list(set(initial_new + additional_new))

        print(f"\n✅ **전체 증상 요약**")
        if all_known:
            print(f"- 일반 증상: {', '.join(all_known)}")
        if all_new:
            print(f"- 특이 증상/행동: {', '.join(all_new)}")

        return all_known, all_new
    else:
        print("추가 증상이 명확하게 파악되지 않았습니다.")
        return initial_known, initial_new


def get_cache_key(symptoms: List[str]) -> str:
    """증상 리스트를 캐시 키로 변환"""
    return ",".join(sorted(symptoms))


def rule_based_disease_mapping(
    symptoms: List[str], confidence_threshold: float = 0.3
) -> Optional[List[tuple]]:
    """
    3단계: Rule 기반 질병 매핑 (캐싱 추가)
    """
    if not symptoms:
        return None

    # 캐시 확인
    cache_key = get_cache_key(symptoms)
    if cache_key in symptom_cache:
        print("💾 캐시된 결과를 사용합니다.")
        return symptom_cache[cache_key]

    results = match_diseases(symptoms, top_k=3)

    # 신뢰도가 낮으면 None 반환 (GPT 추론으로 fallback)
    if not results or results[0][1] < confidence_threshold:
        symptom_cache[cache_key] = None
        return None

    # 결과 캐싱
    symptom_cache[cache_key] = results
    return results


def parse_predicted_diseases(gpt_response: str) -> List[str]:
    """GPT 응답에서 질병 목록을 파싱합니다."""
    diseases = []
    try:
        # "**의심 질병 (1-3개)**" 또는 "**의심 질병**" 섹션 찾기
        disease_section_start = -1
        keywords_to_find = ["**의심 질병 (1-3개)**", "**의심 질병**"]  # 순서대로 찾기
        for key in keywords_to_find:
            disease_section_start = gpt_response.find(key)
            if disease_section_start != -1:
                break

        if disease_section_start != -1:
            # 다음 섹션 키워드로 질병 목록의 끝을 찾음
            next_section_keywords = [
                "**추가 관찰사항**",
                "**권장사항**",
                "**자세한 설명**",
            ]
            disease_section_end = len(gpt_response)

            temp_block_for_search = gpt_response[disease_section_start:]

            for keyword in next_section_keywords:
                end_pos = temp_block_for_search.find(keyword)
                if end_pos != -1:
                    disease_section_end = min(
                        disease_section_end, disease_section_start + end_pos
                    )  # 원본 문자열 기준

            # 실제 질병 목록이 시작되는 부분을 찾기 위해 첫 줄바꿈 이후부터 탐색
            disease_text_block = gpt_response[disease_section_start:disease_section_end]
            first_newline_in_block = disease_text_block.find("\n")
            if first_newline_in_block != -1:
                disease_text_block = disease_text_block[first_newline_in_block:]

            # 정규표현식으로 "숫자. 질병명:" 또는 "숫자. 질병명 (추가정보):" 패턴 찾기
            # 질병명에 괄호 안 내용도 포함 가능하도록 수정
            pattern = re.compile(r"^\s*\d+\.\s*([^:]+?)(?:\s*:\s*|$)", re.MULTILINE)
            matches = pattern.findall(disease_text_block)
            diseases = [
                match.strip() for match in matches if match.strip()
            ]  # 빈 문자열 제거
    except Exception as e:
        print(f"GPT 응답에서 질병 파싱 중 오류 발생: {e}")
    return diseases


def gpt_disease_inference(
    known_symptoms: List[str], new_symptoms: List[str], user_input_for_context: str
) -> str:
    """
    4단계: GPT-4로 질병 추론 (새로운 증상 고려, user_input_for_context 추가)
    """
    all_symptoms_combined = sorted(
        list(set(known_symptoms + new_symptoms))
    )  # 중복 제거 후 정렬
    cache_key = f"gpt_{get_cache_key(all_symptoms_combined)}_{hash(user_input_for_context)}"  # 컨텍스트도 캐시에 영향

    if cache_key in symptom_cache:
        print("💾 캐시된 AI 분석 결과를 사용합니다.")
        return symptom_cache[cache_key]

    prompt = f"""
너는 수의학 전문가야.

보호자의 최초 질문: "{user_input_for_context}"

파악된 증상:
- 일반적인 증상: {', '.join(known_symptoms) if known_symptoms else "없음"}
- 특이 증상/행동: {', '.join(new_symptoms) if new_symptoms else "없음"}

이 증상들을 바탕으로 다음 형식으로 답변해줘:

**의심 질병 (1-3개)**
1. [질병명]: [간단한 설명]
2. [질병명]: [간단한 설명]

**추가 관찰사항**
- [관찰할 점 1]
- [관찰할 점 2]

**권장사항**
- 수의사 상담 필요 여부와 응급도
- 가정에서 할 수 있는 응급처치 (구체적으로)

특이 증상/행동도 고려하여 종합적으로 판단해줘. 답변은 명확하고 완전하게 제공해줘.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=700,  # 최대 토큰 증가
        )

        result = response.choices[0].message.content

        # 결과 캐싱
        symptom_cache[cache_key] = result
        return result

    except Exception as e:
        return f"죄송합니다. 현재 AI 분석에 문제가 있습니다. 수의사와 직접 상담받으시길 권장합니다. (오류: {e})"


def get_disease_description(disease_name: str) -> str:
    """
    5단계: DB에서 질병 설명 검색
    """
    return DISEASE_DESCRIPTIONS.get(
        disease_name,
        f"{disease_name}에 대한 자세한 정보는 수의사와 상담하시기 바랍니다.",
    )


def format_rule_based_response(results: List[tuple]) -> str:
    """
    Rule 기반 결과를 포맷팅
    """
    response = "🔍 **증상 분석 결과 (Rule 기반)**\n\n"

    for i, (disease, confidence) in enumerate(results, 1):
        response += f"**{i}. {disease}** (신뢰도: {confidence*100:.1f}%)\n"
        response += f"{get_disease_description(disease)}\n\n"

    response += "💡 **권장사항**\n"
    response += "- 증상이 지속되거나 악화되면 즉시 수의사와 상담하세요\n"
    response += "- 추가 증상을 관찰하여 기록해두세요\n"

    return response


def vetgpt_chatbot(user_input: str, interactive_mode: bool = True) -> Union[str, Dict]:
    """
    메인 챗봇 함수 - 전체 플로우 실행
    interactive_mode가 False이면 추가 증상 질문 없이 진행하고, 구조화된 결과 반환
    """
    try:
        # 1단계: GPT-4로 증상 추출 (일반 증상과 새로운 증상 구분)
        if interactive_mode:
            print("🔍 증상을 분석중입니다...")
        known_symptoms, new_symptoms = extract_symptoms_with_gpt(user_input)

        all_known = known_symptoms
        all_new = new_symptoms

        if interactive_mode:
            # 2단계: 추가 증상 문의 (대화형 모드에서만)
            all_known, all_new = ask_for_additional_symptoms(
                known_symptoms, new_symptoms
            )

        # 3단계: Rule 기반 질병 매핑 (일반 증상만 사용)
        if interactive_mode:
            print("\n📋 질병 데이터베이스와 매칭중입니다...")
        rule_results = rule_based_disease_mapping(all_known) if all_known else None

        final_response_str = ""
        predicted_diseases_for_output = []  # 최종 예측 질병 목록 (룰 또는 GPT)
        rule_based_raw_output = None
        gpt_raw_output = ""

        if rule_results:
            if interactive_mode:
                print("✅ Rule 기반 매칭 성공!")
            final_response_str = format_rule_based_response(rule_results)
            predicted_diseases_for_output = [res[0] for res in rule_results]
            rule_based_raw_output = rule_results
        else:
            if interactive_mode:
                print("🤖 AI로 종합 분석중입니다...")
            gpt_raw_output = gpt_disease_inference(
                all_known, all_new, user_input
            )  # user_input을 context로 전달
            final_response_str = gpt_raw_output
            predicted_diseases_for_output = parse_predicted_diseases(gpt_raw_output)

        return final_response_str  # 대화형 모드에서는 최종 문자열 응답만

    except Exception as e:
        return f"죄송합니다. 시스템 오류가 발생했습니다. 수의사와 직접 상담받으시길 권장합니다. (오류: {e})"


def clear_cache():
    """캐시 초기화"""
    global symptom_cache
    symptom_cache = {}
    print("🗑️ 캐시가 초기화되었습니다.")


class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
        # 대화 상태 관리를 위한 딕셔너리
        # {chat_room_id: {"state": "waiting_for_additional", "symptoms": {"known": [...], "new": [...]}}}
        self.chat_states = {}

    def get_dog_info(self, user_id: int) -> Optional[dict]:
        """사용자의 반려견 정보 조회"""
        dog = (
            self.db.query(Dog)
            .options(
                joinedload(Dog.breed),
                joinedload(Dog.diseases),
                joinedload(Dog.allergies),
            )
            .filter(Dog.user_id == user_id, Dog.deleted_at.is_(None))
            .first()
        )
        if not dog:
            return None

        # 질병 이름 추출 - static map 사용
        disease_names = []
        if dog.diseases:
            for dd in dog.diseases:
                disease_id = str(dd.disease_id)
                if disease_id in DISEASE_MAP:
                    disease_names.append(DISEASE_MAP[disease_id])

        # 알러지 이름 추출 - static map 사용
        allergy_names = []
        if dog.allergies:
            for da in dog.allergies:
                allergy_id = str(da.allergy_id)
                if allergy_id in ALLERGY_MAP:
                    allergy_names.append(ALLERGY_MAP[allergy_id])

        return {
            "name": dog.name,
            "breed": dog.breed.name if dog.breed else None,
            "age": dog.age_group,
            "weight": dog.weight,
            "gender": dog.gender,
            "diseases": disease_names,
            "allergies": allergy_names,
        }

    def create_chat_room(self, chat_room_data: ChatRoomCreate) -> ChatRoom:
        """새로운 대화방 생성"""
        chat_room = ChatRoom(user_id=chat_room_data.user_id, title=chat_room_data.title)
        self.db.add(chat_room)
        self.db.commit()
        self.db.refresh(chat_room)
        return chat_room

    def get_chat_rooms(self, user_id: int) -> List[ChatRoom]:
        """사용자의 대화방 목록 조회"""
        return (
            self.db.query(ChatRoom)
            .filter(ChatRoom.user_id == user_id, ChatRoom.deleted_at.is_(None))
            .order_by(ChatRoom.updated_at.desc())
            .all()
        )

    def get_chat_history(self, chat_room_id: UUID) -> List[ChatMessage]:
        """대화방의 대화 내역 조회"""
        chat_room = (
            self.db.query(ChatRoom)
            .filter(ChatRoom.id == chat_room_id, ChatRoom.deleted_at.is_(None))
            .first()
        )
        if not chat_room:
            return []

        return (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.chat_room_id == chat_room_id,
                ChatMessage.deleted_at.is_(None),
            )
            .order_by(ChatMessage.created_at)
            .all()
        )

    def delete_chat_room(self, chat_room_id: UUID):
        """대화방 삭제 (soft delete)"""
        chat_room = (
            self.db.query(ChatRoom)
            .filter(ChatRoom.id == chat_room_id, ChatRoom.deleted_at.is_(None))
            .first()
        )
        if chat_room:
            chat_room.deleted_at = datetime.utcnow()
            # 관련된 메시지와 증상 로그도 함께 soft delete
            self.db.query(ChatMessage).filter(
                ChatMessage.chat_room_id == chat_room_id,
                ChatMessage.deleted_at.is_(None),
            ).update({"deleted_at": datetime.utcnow()})
            self.db.query(SymptomLog).filter(
                SymptomLog.chat_room_id == chat_room_id, SymptomLog.deleted_at.is_(None)
            ).update({"deleted_at": datetime.utcnow()})
            self.db.commit()

    async def process_message(
        self, chat_room_id: UUID, message_data: ChatMessageCreate
    ) -> ChatMessage:
        """사용자 메시지 처리 및 챗봇 응답 생성"""
        # 채팅방 존재 여부 확인
        chat_room = (
            self.db.query(ChatRoom)
            .filter(ChatRoom.id == chat_room_id, ChatRoom.deleted_at.is_(None))
            .first()
        )
        if not chat_room:
            raise ValueError("Chat room not found or deleted")

        # 사용자 메시지 저장
        user_message = ChatMessage(
            chat_room_id=chat_room_id,
            user_id=message_data.user_id,
            role="user",
            content=message_data.content,
        )
        self.db.add(user_message)

        # 반려견 정보 조회
        dog_info = self.get_dog_info(message_data.user_id)

        # 이전 대화 내역 조회
        chat_history = self.get_chat_history(chat_room_id)

        # 현재 대화 상태 확인
        current_state = self.chat_states.get(str(chat_room_id), {"state": "initial"})

        if current_state["state"] == "initial":
            # 첫 메시지 처리
            known_symptoms, new_symptoms = self._extract_symptoms_with_gpt(
                message_data.content
            )

            # 대화 상태 업데이트
            self.chat_states[str(chat_room_id)] = {
                "state": "waiting_for_additional",
                "symptoms": {"known": known_symptoms, "new": new_symptoms},
            }

            # 추가 증상 문의 메시지 생성
            response_content = self._generate_additional_symptoms_prompt(
                known_symptoms, new_symptoms
            )
        elif current_state["state"] == "waiting_for_additional":
            # 추가 증상 처리
            additional_known, additional_new = self._extract_symptoms_with_gpt(
                message_data.content
            )

            # 기존 증상과 추가 증상 합치기
            all_known = list(set(current_state["symptoms"]["known"] + additional_known))
            all_new = list(set(current_state["symptoms"]["new"] + additional_new))

            # 대화 상태 초기화
            self.chat_states[str(chat_room_id)] = {"state": "initial"}

            # 최종 응답 생성
            response_content = self._generate_response(
                message_data.content, all_known, all_new, dog_info, chat_history
            )

        # 챗봇 응답 저장
        assistant_message = ChatMessage(
            chat_room_id=chat_room_id,
            user_id=message_data.user_id,
            role="assistant",
            content=response_content,
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)

        return assistant_message

    def _generate_additional_symptoms_prompt(
        self, known_symptoms: List[str], new_symptoms: List[str]
    ) -> str:
        """추가 증상 문의 메시지 생성"""
        response = "🔍 **파악된 증상**\n"

        if known_symptoms:
            response += f"\n일반적인 증상:\n- {', '.join(known_symptoms)}"
        if new_symptoms:
            response += f"\n\n특이 증상/행동:\n- {', '.join(new_symptoms)}"

        response += "\n\n💬 **추가 증상이나 상태가 있나요?**\n"
        response += "- 예: 열이 있어요, 기침을 해요, 설사를 해요 등\n"
        response += "- 특이한 행동이나 상태 변화도 알려주세요!\n"
        response += "- 없으시다면 '없음'이라고 답변해주세요."

        return response

    def _extract_symptoms_with_gpt(
        self, user_input: str
    ) -> Tuple[List[str], List[str]]:
        """GPT를 사용하여 증상 추출"""
        prompt = f"""
너는 수의학 전문가야. 보호자의 말에서 반려동물의 모든 증상을 추출해줘.

보호자 말: "{user_input}"

다음 형식으로 JSON 응답을 생성해줘:
{{
    "known_symptoms": ["기존 증상1", "기존 증상2"],  # 일반적으로 알려진 증상
    "new_symptoms": ["새로운 증상1", "새로운 증상2"]  # 특이하거나 새로운 증상/행동
}}
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
            )

            result = json.loads(response.choices[0].message.content)
            return normalize_symptoms(result.get("known_symptoms", [])), result.get(
                "new_symptoms", []
            )
        except Exception as e:
            print(f"GPT 증상 추출 오류: {e}")
            return [], []

    def _generate_response(
        self,
        user_input: str,
        known_symptoms: List[str],
        new_symptoms: List[str],
        dog_info: Optional[dict],
        chat_history: List[ChatMessage],
    ) -> str:
        """챗봇 응답 생성"""
        # Rule 기반 질병 매칭 시도
        rule_results = match_diseases(known_symptoms) if known_symptoms else None

        if rule_results and rule_results[0][1] >= 0.3:  # 신뢰도 30% 이상
            return self._format_rule_based_response(rule_results, dog_info)

        # GPT를 통한 응답 생성
        return self._generate_gpt_response(
            user_input, known_symptoms, new_symptoms, dog_info, chat_history
        )

    def _format_rule_based_response(
        self, results: List[tuple], dog_info: Optional[dict]
    ) -> str:
        """Rule 기반 결과 포맷팅"""
        response = "🔍 **증상 분석 결과**\n\n"

        if dog_info:
            response += f"반려견 정보:\n"
            response += f"- 이름: {dog_info.get('name', '정보 없음')}\n"
            response += f"- 품종: {dog_info.get('breed', '정보 없음')}\n"
            response += f"- 나이: {dog_info.get('age', '정보 없음')}세\n"
            response += f"- 체중: {dog_info.get('weight', '정보 없음')}kg\n"
            response += f"- 성별: {dog_info.get('gender', '정보 없음')}\n"
            if dog_info.get("diseases"):
                response += f"- 기존 질병: {', '.join(dog_info['diseases'])}\n"
            if dog_info.get("allergies"):
                response += f"- 알러지: {', '.join(dog_info['allergies'])}\n"
            response += "\n"

        for i, (disease, confidence) in enumerate(results, 1):
            response += f"**{i}. {disease}** (신뢰도: {confidence*100:.1f}%)\n"
            response += f"{DISEASE_DESCRIPTIONS.get(disease, '상세 정보가 필요한 경우 수의사와 상담하세요.')}\n\n"

        response += "💡 **권장사항**\n"
        response += "- 증상이 지속되거나 악화되면 즉시 수의사와 상담하세요\n"
        response += "- 추가 증상이 있다면 알려주세요\n"

        return response

    def _generate_gpt_response(
        self,
        user_input: str,
        known_symptoms: List[str],
        new_symptoms: List[str],
        dog_info: Optional[dict],
        chat_history: List[ChatMessage],
    ) -> str:
        """GPT를 통한 응답 생성"""
        # 대화 히스토리 포맷팅
        formatted_history = "\n".join(
            [
                f"{'보호자' if msg.role == 'user' else '수의사'}: {msg.content}"
                for msg in chat_history[-5:]  # 최근 5개 메시지만
            ]
        )

        # 반려견 정보 포맷팅
        dog_info_str = ""
        if dog_info:
            dog_info_str = f"""
반려견 정보:
- 이름: {dog_info.get('name', '정보 없음')}
- 품종: {dog_info.get('breed', '정보 없음')}
- 나이: {dog_info.get('age', '정보 없음')}세
- 체중: {dog_info.get('weight', '정보 없음')}kg
- 성별: {dog_info.get('gender', '정보 없음')}
- 기존 질병: {', '.join(dog_info.get('diseases', []) or ['없음'])}
- 알러지: {', '.join(dog_info.get('allergies', []) or ['없음'])}
"""

        prompt = f"""
너는 수의학 전문가야. 다음 정보를 바탕으로 답변해줘:

{dog_info_str}

최근 대화 내역:
{formatted_history}

현재 질문: {user_input}

파악된 증상:
- 일반 증상: {', '.join(known_symptoms) if known_symptoms else '없음'}
- 특이 증상: {', '.join(new_symptoms) if new_symptoms else '없음'}

다음 형식으로 답변해줘:

**의심 질병 (1-3개)**
1. [질병명]: [간단한 설명]
2. [질병명]: [간단한 설명]

**추가 관찰사항**
- [관찰할 점 1]
- [관찰할 점 2]

**권장사항**
- 수의사 상담 필요 여부와 응급도
- 가정에서 할 수 있는 응급처치 (구체적으로)
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=700,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"죄송합니다. 현재 AI 분석에 문제가 있습니다. 수의사와 직접 상담받으시길 권장합니다. (오류: {e})"

    def update_room_title(self, chat_room_id: UUID, title: str):
        """대화방 제목 업데이트"""
        chat_room = self.db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
        if chat_room:
            chat_room.title = title
            self.db.commit()

    def get_chat_rooms_with_last_message(self, user_id: int) -> List[ChatRoomResponse]:
        """사용자의 대화방 목록을 마지막 메시지와 함께 조회"""
        chat_rooms = (
            self.db.query(ChatRoom)
            .filter(ChatRoom.user_id == user_id, ChatRoom.deleted_at.is_(None))
            .order_by(ChatRoom.updated_at.desc())
            .all()
        )

        result = []
        for room in chat_rooms:
            # 마지막 메시지 조회
            last_message = (
                self.db.query(ChatMessage)
                .filter(
                    ChatMessage.chat_room_id == room.id,
                    ChatMessage.deleted_at.is_(None),
                )
                .order_by(ChatMessage.created_at.desc())
                .first()
            )

            result.append(
                ChatRoomResponse(
                    id=room.id,
                    title=room.title,
                    created_at=room.created_at,
                    updated_at=room.updated_at,
                    deleted_at=room.deleted_at,
                    last_message=last_message.content if last_message else None,
                )
            )

        return result

    def get_chat_history_with_dog_info(
        self, chat_room_id: UUID, user_id: int
    ) -> ChatHistoryResponse:
        """대화 내역과 반려견 정보를 함께 조회"""
        messages = self.get_chat_history(chat_room_id)
        dog_info = self.get_dog_info(user_id)

        return ChatHistoryResponse(messages=messages, dog_info=dog_info)

    def create_symptom_log(self, symptom_data: SymptomLogCreate) -> SymptomLog:
        """증상 로그 생성"""
        symptom_log = SymptomLog(
            chat_room_id=symptom_data.chat_room_id,
            user_id=symptom_data.user_id,
            symptom_name=symptom_data.symptom_name,
            context=symptom_data.context,
        )
        self.db.add(symptom_log)
        self.db.commit()
        self.db.refresh(symptom_log)
        return symptom_log


if __name__ == "__main__":
    print("🐾 VetGPT 챗봇이 시작되었습니다!")
    print("종료하려면 'quit' 또는 'exit'을 입력하세요.")
    print("캐시를 초기화하려면 'clear'를 입력하세요.\n")

    while True:
        user_question = input("💬 반려동물 상태를 알려주세요: ")

        if user_question.lower() in ["quit", "exit", "종료"]:
            print("챗봇을 종료합니다. 반려동물 건강에 유의하세요! 🐾")
            break
        elif user_question.lower() == "clear":
            clear_cache()
            continue

        if user_question.strip():
            print("\n" + "=" * 50)
            response = vetgpt_chatbot(user_question, interactive_mode=True)
            print(response)
            print("=" * 50 + "\n")

# 🧪 리포트 API 테스트 가이드

## 📖 **개요**
리포트 API의 동작을 검증하기 위한 다양한 테스트 방법을 제공합니다.

---

## 🚀 **1단계: 환경 준비**

### **1️⃣ 필수 패키지 설치**
```bash
pip install requests pytest pytest-asyncio
```

### **2️⃣ 데이터베이스 마이그레이션**
```bash
# 마이그레이션 생성 (아직 안했다면)
alembic revision --autogenerate -m "Add numeric_value and unit to HealthCheck model"

# 마이그레이션 실행
alembic upgrade head
```

### **3️⃣ FastAPI 서버 실행**
```bash
uvicorn api.main:app --reload
```

---

## 🎯 **2단계: 테스트 실행**

### **방법 1: 더미 데이터 생성 + API 테스트 (추천!)**

#### **1️⃣ 더미 데이터 생성**
```bash
# 방법 1: 모듈로 실행 (권장)
python -m api.scripts.create_test_data

# 방법 2: 직접 실행 (루트 파일)
python test_report_data.py
```

**결과 예시:**
```
🚀 더미 데이터 생성 시작...
✅ 테스트 사용자 생성
✅ 테스트 견종 생성
✅ 테스트 강아지 생성
📊 건강 체크 데이터 생성 중...
🚶 산책 데이터 생성 중...
🍽️ 사료/물 데이터 생성 중...
⚖️ 체중 데이터 생성 중...
✅ 더미 데이터 생성 완료!

📋 테스트 계정 정보:
   이메일: test@bethe.pet
   비밀번호: testpassword
   강아지: 멍멍이 (ID: 1)
```

#### **2️⃣ API 테스트 실행**
```bash
# 방법 1: pytest로 실행 (권장)
pytest tests/test_api_integration.py -v

# 방법 2: 직접 실행
python tests/test_api_integration.py

# 방법 3: 루트 파일 실행
python test_report_api.py
```

**결과 예시:**
```
🧪 리포트 API 테스트 도구
✅ 서버 연결 확인

🚀 리포트 API 테스트 시작
==================================================
🔐 로그인 시도: test@bethe.pet
✅ 로그인 성공!

📊 종합 리포트 테스트 (period: week)
✅ 종합 리포트 성공!
   건강 점수: 78점
   건강 상태: 보통
   인사이트 개수: 4
   산책 횟수: 5회
   사료 급여: 7회

🧠 건강 인사이트 테스트 (period: week)
✅ 건강 인사이트 성공!
   건강 점수: 78점
   상태: 보통

🏃 활동 통계 테스트 (period: month)
✅ 활동 통계 성공!
   산책: 10회
   평균 거리: 2.8km

✅ 모든 테스트 완료!
```

---

### **방법 2: pytest 단위 테스트**

```bash
# 특정 테스트 파일 실행
pytest tests/test_report_service.py -v

# 전체 테스트 실행
pytest tests/ -v

# 커버리지와 함께 실행
pytest tests/test_report_service.py --cov=api.services.report_service --cov-report=html
```

**결과 예시:**
```
========================= test session starts =========================
tests/test_report_service.py::TestReportService::test_calculate_health_score_numeric_data PASSED
tests/test_report_service.py::TestReportService::test_calculate_health_score_status_data PASSED
tests/test_report_service.py::TestReportService::test_numeric_to_status_conversion_sleep PASSED
tests/test_report_service.py::TestReportService::test_generate_insights_with_data PASSED
========================= 12 passed in 0.45s =========================
```

---

### **방법 3: 수동 API 호출 테스트**

#### **1️⃣ 로그인 토큰 획득**
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@bethe.pet&password=testpassword"
```

#### **2️⃣ 리포트 API 호출**
```bash
# 종합 리포트
curl -X GET "http://localhost:8000/report/comprehensive?period=week" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 건강 인사이트
curl -X GET "http://localhost:8000/report/insight?period=month" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 활동 통계
curl -X GET "http://localhost:8000/report/activities?period=all" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🔍 **3단계: 응답 데이터 분석**

### **종합 리포트 응답 구조**
```json
{
  "health_insight": {
    "score": 78,
    "status": "보통",
    "insights": [
      "멍멍이의 평균 수면시간은 7.2시간으로 적정 수준입니다.",
      "체온이 정상 범위에 있어 건강상태가 양호합니다.",
      "식욕 상태에 주의가 필요합니다."
    ]
  },
  "activity_stats": {
    "walk_count": 5,
    "total_walk_distance": 14.2,
    "avg_walk_distance": 2.84,
    "avg_walk_duration": 37.6,
    "feed_count": 7,
    "avg_food_amount": 125.7,
    "avg_water_intake": 325.0,
    "latest_weight": 25.5
  }
}
```

### **건강 상세 응답 구조**
```json
[
  {
    "item": "수면",
    "status": "정상",
    "average_numeric": 7.25,
    "unit": "시간",
    "recent_trend": "안정",
    "data_count": 4
  },
  {
    "item": "식욕",
    "status": "주의",
    "normal_count": 3,
    "warning_count": 2,
    "abnormal_count": 0,
    "data_count": 5
  }
]
```

---

## ⚠️ **문제 해결**

### **자주 발생하는 오류들**

#### **1️⃣ 서버 연결 실패**
```
❌ 서버에 연결할 수 없습니다. FastAPI 서버를 먼저 실행하세요.
```
**해결법:** `uvicorn api.main:app --reload` 실행

#### **2️⃣ 로그인 실패**
```
❌ 로그인 실패: 401 - {"detail":"Incorrect email or password"}
```
**해결법:** 더미 데이터 생성 스크립트를 다시 실행

#### **3️⃣ 데이터 없음 오류**
```
❌ 종합 리포트 실패: 404 - {"detail":"Dog not found"}
```
**해결법:** 더미 데이터가 올바르게 생성되었는지 확인

#### **4️⃣ 마이그레이션 오류**
```
sqlalchemy.exc.OperationalError: no such column: health_checks.numeric_value
```
**해결법:** `alembic upgrade head` 실행

---

## 📊 **테스트 커버리지**

### **테스트하는 기능들**
- ✅ 로그인/인증
- ✅ 수치형 데이터 처리 (수면, 체온)
- ✅ 상태형 데이터 처리 (식욕, 활력, 배변)
- ✅ 건강 점수 계산
- ✅ 인사이트 생성
- ✅ 활동 통계 계산
- ✅ 기간별 필터링 (week/month/all)
- ✅ 에러 처리
- ✅ NULL 값 처리

### **테스트 시나리오**
1. **정상 동작**: 모든 데이터가 정상적으로 있는 경우
2. **부분 데이터**: 일부 항목만 데이터가 있는 경우
3. **빈 데이터**: 데이터가 전혀 없는 경우
4. **혼합 데이터**: 수치형과 상태형이 혼재된 경우
5. **에러 케이스**: 잘못된 입력값, 인증 실패 등

---

## 🎉 **테스트 성공 기준**

### **API 테스트**
- ✅ 모든 엔드포인트가 200 응답
- ✅ 응답 데이터 구조가 올바름
- ✅ 건강 점수가 0-100 범위
- ✅ 인사이트가 생성됨
- ✅ 통계 데이터가 계산됨

### **단위 테스트**
- ✅ 모든 테스트 케이스 통과
- ✅ 엣지 케이스 처리 확인
- ✅ 데이터 변환 로직 검증
- ✅ NULL 값 안전성 확인

이제 **원하는 방법으로 테스트**를 진행해보세요! 🚀 
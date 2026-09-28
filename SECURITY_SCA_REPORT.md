# SCA 의존성 보안 점검 및 업데이트 보고서

- 점검일: 2026-09-29
- 반영 대상: GitHub 기본 브랜치 `develop`
- 원본 보안 브랜치: `security/sast-remediation-20260929`
- 도구: Poetry 2.2.0, pip-audit 2.10.1
- 최종 산출물: `pip-audit.after.json`, `chatbot/pip-audit.chatbot.after.json`

## 결과

| 구분 | 결과 |
|---|---:|
| GitHub Dependabot 기본 브랜치 병합 전 | 106건 |
| 병합된 `develop` 루트 환경 pip-audit (49개 패키지) | 0건 |
| 병합된 `develop` 챗봇 환경 pip-audit (52개 패키지) | 0건 |
| Semgrep `auto` | 0건 |

GitHub의 106건은 병합 전 기본 브랜치 기준이다. 보안 브랜치가 `release/2` 계열에서 생성되어 있어 일반 merge 시 무관한 `Prod` 커밋과 56개 파일 변경이 함께 들어오는 구조였다. 따라서 보안 커밋 `820bcff`, `0eadc69`만 `develop`에 선택 병합하고, `develop` 의존성을 기준으로 두 lockfile을 새로 해석했다. 루트와 `chatbot/` 가상환경 모두 `No known vulnerabilities found`를 확인했다.

## 핵심 업데이트·교체

- FastAPI `0.110.3` → `0.141.1`
- Starlette `0.37.2` → `1.7.0`
- Pillow `11.2.1` → `12.3.0`
- python-multipart `0.0.20` → `0.0.32`
- pytest `8.4.0` → `9.1.1`
- pytest-asyncio `0.23.8` → `1.4.0`
- Uvicorn `0.29.0` → `0.54.0`
- SQLAlchemy `2.0.41` → `2.0.54` (`<2.1` 호환 범위 고정)
- python-jose/ecdsa 계열 제거, PyJWT `2.15.0`으로 교체

저장소에는 루트와 `chatbot/`에 독립적인 `poetry.lock`이 있다. 첫 감사에서 루트만 갱신하면 챗봇 이미지가 계속 FastAPI 0.110.3, Pillow 11.2.1, python-jose 3.5.0 등을 설치하는 사실을 전체 Docker 빌드 로그로 발견했다. 챗봇에도 동일한 보안 버전 범위를 적용하고 전체 전이 의존성을 `poetry update`했다. 공용 `api` 코드를 import할 때 필요한 PyJWT도 챗봇 의존성에 명시했다.

`python-jose` 의 전이 의존성 `ecdsa` 경고에는 pip-audit이 수정 버전을 제시하지 못했다. 코드가 HS256 JWT 발급·검증만 사용하므로, 동일 API를 제공하는 PyJWT로 교체하고 예외를 `ExpiredSignatureError`, `InvalidTokenError`로 변경했다. 이로써 사용하지 않는 ecdsa, pyasn1, rsa도 환경에서 제거됐다.

전체 업데이트에서 SQLAlchemy 2.1이 기존 `postgresql://` URL에 대해 Psycopg 3를 선택해 앱 import가 실패하는 회귀를 발견했다. 새 DB 드라이버를 추가하는 대신 기존 `psycopg2-binary`와 호환되는 SQLAlchemy 2.0 최신 패치로 제한했다. 또한 Pydantic v2의 폐기 경고를 없애기 위해 `orm_mode` 설정을 `from_attributes`로 변경했다.

```python
import jwt

token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

## 검증

- `pip-audit`: 루트 49개와 챗봇 52개 패키지 각각 0건
- Python `compileall`: 통과
- 기존 food recommender 테스트: `1 passed`
- PyJWT access-token 발급→검증 round-trip: 통과
- 변조/만료 JWT 예외 처리 및 FastAPI 전체 app import: 통과
- 챗봇 전체 이미지 빌드, FastAPI app import와 CORS allowlist 확인: 통과
- `poetry check`: 유효, Poetry의 신규 PEP 621 전환 권고만 존재

전체 pytest 수집은 기존 `chatbot/tests/websocket_test.py`가 선언되지 않은 `websockets` 테스트 의존성을 요구해 중단됐다. chatbot을 제외한 기존 `tests/`는 현재 `ReportService` 생성자와 테스트가 불일치하고, 통합 테스트가 미기동 localhost 서버를 요구해 `1 passed, 3 skipped, 1 failed, 13 errors`였다. 이는 보안 수정 코드와 무관한 기존 테스트 인프라/구현 불일치로 별도 수정이 필요하다.

기존 테스트 파일은 패키지 import가 아니어서 다음과 같이 기존 경로 보정을 유지해 실행했다.

```bash
PYTHONPATH=api/foodrecomender .venv/bin/python -m pytest -q \
  api/foodrecomender/test_example.py
```

## 지속 관리

`.github/dependabot.yml`에 Poetry/pip과 GitHub Actions 주간 검사를 추가했다. Dependabot은 외부 침입 봇이 아니라 GitHub의 보안 서비스이며, 임의 코드를 바로 병합하지 않고 업데이트 PR을 제안한다. 자동 병합은 설정하지 않았다.

# SCA 의존성 보안 점검 및 업데이트 보고서

- 점검일: 2026-09-29
- 브랜치: `security/sast-remediation-20260929`
- 도구: Poetry 2.2.0, pip-audit 2.10.1
- 기준/최종 산출물: `pip-audit.before.json`, `pip-audit.after.json`

## 결과

| 구분 | 취약 패키지 | CVE/별칭 레코드 |
|---|---:|---:|
| 업데이트 전 가상환경 | 15 | 118 |
| 제약 내 일차 업데이트 | 6 | 77 |
| 제약 조정·라이브러리 교체 후 | 0 | 0 |

GitHub의 106건은 기본 브랜치 기준이고, 로컬 118건은 가상환경의 CVE 별칭을 모두 세어 계산 방식이 다르다. 최종 `.venv`에서 `No known vulnerabilities found`를 확인했다. GitHub 경고는 이 브랜치가 기본 브랜치에 병합된 후 갱신된다.

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

`python-jose` 의 전이 의존성 `ecdsa` 경고에는 pip-audit이 수정 버전을 제시하지 못했다. 코드가 HS256 JWT 발급·검증만 사용하므로, 동일 API를 제공하는 PyJWT로 교체하고 예외를 `ExpiredSignatureError`, `InvalidTokenError`로 변경했다. 이로써 사용하지 않는 ecdsa, pyasn1, rsa도 환경에서 제거됐다.

전체 업데이트에서 SQLAlchemy 2.1이 기존 `postgresql://` URL에 대해 Psycopg 3를 선택해 앱 import가 실패하는 회귀를 발견했다. 새 DB 드라이버를 추가하는 대신 기존 `psycopg2-binary`와 호환되는 SQLAlchemy 2.0 최신 패치로 제한했다. 또한 Pydantic v2의 폐기 경고를 없애기 위해 `orm_mode` 설정을 `from_attributes`로 변경했다.

```python
import jwt

token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

## 검증

- `pip-audit`: 118→0
- Python `compileall`: 통과
- 기존 food recommender 테스트: `1 passed`
- PyJWT access-token 발급→검증 round-trip: 통과
- 변조/만료 JWT 예외 처리 및 FastAPI 전체 app import: 통과
- `poetry check`: 유효, Poetry의 신규 PEP 621 전환 권고만 존재

기존 테스트 파일은 패키지 import가 아니어서 다음과 같이 기존 경로 보정을 유지해 실행했다.

```bash
PYTHONPATH=api/foodrecomender .venv/bin/python -m pytest -q \
  api/foodrecomender/test_example.py
```

## 지속 관리

`.github/dependabot.yml`에 Poetry/pip과 GitHub Actions 주간 검사를 추가했다. Dependabot은 외부 침입 봇이 아니라 GitHub의 보안 서비스이며, 임의 코드를 바로 병합하지 않고 업데이트 PR을 제안한다. 자동 병합은 설정하지 않았다.

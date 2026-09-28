# BethePet 보안 점검 최종 보고서

- 점검일: 2026-09-29
- 대상 저장소: `BeThePet/Backend`
- 최종 기준 브랜치: `develop`
- 최종 반영 커밋: `3c4cd31`

## 최종 결론

보안 브랜치의 변경을 그대로 병합하지 않고, 보안 수정 커밋만 `develop`에 선별 반영했다. 전체 브랜치 병합은 56개 파일 변경과 11개 충돌을 만들며 챗봇 코드 삭제, lockfile 충돌, Nginx·보고서 충돌을 포함하므로 추가 병합하지 않는다.

현재 `develop`은 다음 상태다.

| 점검 항목 | 최종 결과 |
|---|---:|
| GitHub Dependabot 병합 전 | 106건 |
| GitHub Dependabot 재계산 후 열린 경고 | **0건** |
| GitHub Dependabot 닫힌 경고 | 108건(기존 2건 포함) |
| Semgrep `auto` | **0건** |
| 루트 pip-audit | **0건** |
| 챗봇 pip-audit | **0건** |

## 조치한 대표 취약점

1. GitHub Actions의 mutable tag/branch 참조를 커밋 SHA로 고정했다.
2. API·챗봇 컨테이너를 non-root UID 10001로 실행하도록 변경했다.
3. 챗봇의 wildcard CORS를 제거하고 `CHATBOT_CORS_ORIGINS` allowlist로 변경했다.
4. Nginx 일반 API 경로의 불필요한 `Upgrade` 헤더 전달을 제거했다.
5. WebSocket 경로는 임의 Upgrade 값을 전달하지 않고 WebSocket 상수만 허용했다.
6. FastAPI, Starlette, Pillow, python-multipart, Uvicorn, SQLAlchemy 등 취약 의존성을 갱신했다.
7. `python-jose`/`ecdsa` 계열을 제거하고 PyJWT로 교체했다.
8. 루트와 `chatbot/`의 독립 Poetry lockfile을 모두 갱신했다.
9. Dependabot에 Poetry/pip 및 GitHub Actions 주간 검사를 설정했다.

## 검증 결과

- Semgrep 최종 스캔: 120개 파일, 345개 규칙, 0건
- 루트 가상환경: 49개 패키지, pip-audit 0건
- 챗봇 가상환경: 52개 패키지, pip-audit 0건
- Python `compileall`: 통과
- API·챗봇 Docker `build --check`: 통과
- 챗봇 실제 Docker 이미지 빌드: 통과, 실행 사용자 `appuser`
- Nginx `nginx -t`: 통과
- API·챗봇 CORS preflight:
  - `https://yoon.today`: 허용
  - `http://localhost:3000`: 허용
  - 임의 origin: 차단
- PyJWT 발급·검증 및 변조/만료 토큰 예외 처리: 통과

전체 pytest는 기존 테스트 인프라 문제로 완전 통과하지 못했다. `ReportService` 생성자와 테스트가 불일치하고, 통합 테스트는 기동 중인 localhost 서버를 요구한다. 챗봇 WebSocket 테스트도 테스트용 쿠키와 서버가 필요하다. 이는 이번 보안 변경으로 새로 발생한 실패가 아니다.

## 남은 운영 과제

- 실제 AWS RDS를 사용하는 통합 테스트용 PostgreSQL 환경 또는 Docker Compose 테스트 DB를 별도로 마련해야 한다.
- 프런트엔드가 `localhost:5173` 또는 별도 스테이징 도메인을 사용하면 `ALLOWED_ORIGINS`, `CHATBOT_CORS_ORIGINS`, Nginx allowlist에 명시적으로 추가해야 한다.
- Dependabot PR은 자동 병합하지 않고 CI·호환성 검토 후 개별 승인한다.

## 재현 명령

```bash
export SSL_CERT_FILE=/etc/ssl/cert.pem
semgrep --config auto --json -o semgrep_result.after.json .
pip-audit --path .venv/lib/python3.12/site-packages -f json -o pip-audit.after.json
poetry check
docker build --check --progress=plain .
```

# SAST 보안 점검 및 조치 보고서

- 점검일: 2026-09-29
- 반영 대상: GitHub 기본 브랜치 `develop`
- 원본 보안 브랜치: `security/sast-remediation-20260929`
- 도구: Semgrep 1.178.0, Community `auto` 규칙
- 원본/조치 후 산출물: `semgrep_result.before.json`, `semgrep_result.after.json`

## 1. 결과 요약

| 구분 | 검사 파일 | 실행 규칙 | 검출 건수 |
|---|---:|---:|---:|
| 보안 브랜치 조치 전 | 94 | 344 | 5 |
| 보안 브랜치 조치 후 | 101 | 345 | 0 |
| `develop` 선택 병합 후 추가 검출 | 119 | 345 | 5 |
| `develop` 최종 | 120 | 345 | 0 |

첫 5건은 GitHub Actions 가변 참조 4건과 API root 컨테이너 1건이었다. 이후 `develop`에만 있던 챗봇·Nginx 코드까지 통합 스캔해 root 컨테이너 1건, wildcard CORS 1건, H2C smuggling 가능성이 있는 Upgrade 헤더 전달 3건을 추가로 발견했다. 두 단계에서 서로 다른 총 10건을 조치했다.

## 2. 취약점과 해결

### GitHub Actions 가변 태그/브랜치

`checkout` v3, AWS 인증 v1, ECR 로그인 v1, SSH Action `master`를 각 참조가 점검 시점에 가리키던 40자 SHA로 고정했다. 이로써 태그나 브랜치가 나중에 다른 커밋으로 바뀌어도 검토한 코드만 실행된다. 향후 버전 업데이트는 Dependabot 등으로 SHA를 검토해 교체해야 한다.

### root 컨테이너

애플리케이션 코드를 복사한 후 UID 10001의 `appuser`를 만들고 `/app`의 소유권을 이전한 뒤 `USER appuser`로 실행하도록 했다. 의존성 설치는 root 단계에서 유지하고 런타임만 최소 권한으로 바꿔 빌드 호환성과 보안을 같이 유지했다.

```dockerfile
RUN useradd --create-home --uid 10001 appuser \
  && chown -R appuser:appuser /app
USER appuser
```

API와 챗봇 Dockerfile 모두 동일 원칙을 적용했다. 챗봇의 쓰기 경로는 기존 `chmod 777` 대신 UID 10001 사용자에게만 소유권을 주었다.

### 챗봇 CORS

credential 요청과 함께 모든 origin을 허용하던 `allow_origins=["*"]`를 제거했다. 기본값은 실제 프런트엔드와 로컬 개발 주소만 허용하고, 배포 환경에서는 쉼표로 구분한 `CHATBOT_CORS_ORIGINS`로 바꿀 수 있다.

```python
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CHATBOT_CORS_ORIGINS", "http://localhost:3000,https://yoon.today"
    ).split(",")
    if origin.strip()
]
```

### Nginx H2C smuggling 방지

일반 API 프록시에서는 필요하지 않은 `Upgrade`/`Connection: upgrade` 전달을 삭제했다. 로컬 `/ws`는 WebSocket 전용 경로이므로 클라이언트가 보낸 임의 프로토콜 값을 전달하지 않고 `Upgrade websocket` 상수만 백엔드에 보낸다. Semgrep 규칙은 안전한 상수 구성도 동일 패턴으로 검출하므로, 코드 옆에 근거를 기록한 단일 `nosemgrep` 억제를 적용했다.

## 3. 검증과 트러블슈팅

- Semgrep: 보안 브랜치 5→0, `develop` 추가분 5→0, 최종 120개 파일·345개 규칙 0건
- Python `compileall`: 통과
- GitHub Actions YAML 파싱: 통과
- API·챗봇 Docker `build --check`: 경고 0, 통과
- 챗봇 전체 Docker 이미지 빌드 및 Nginx `nginx -t`: 통과
- 챗봇 CORS allowlist 환경변수 적용과 FastAPI app import: 통과
- JSON before/after 유효성: 통과
- `git diff --check`: 통과

첫 `pytest -q`는 `api/foodrecomender/test_example.py`가 패키지 경로가 아닌 `Food_Recommender`를 절대 import해 수집 단계에서 실패했다. 이는 본 보안 수정 전부터 있던 테스트 경로 문제다. 다음과 같이 모듈 경로를 제공해 테스트를 실제 실행했고 `1 passed`를 확인했다.

```bash
PYTHONPATH=api/foodrecomender .venv/bin/python -m pytest -q api/foodrecomender/test_example.py
```

장기적으로는 테스트의 import를 패키지 상대 import로 바꿔 별도 `PYTHONPATH`가 필요 없게 하는 것이 좋다. 해당 파일은 이번 취약점 조치 범위에서는 변경하지 않았다.

## 4. 재현 명령

```bash
export SSL_CERT_FILE=/etc/ssl/cert.pem
/Users/song-yoonju/.venvs/semgrep/bin/semgrep --config auto --json -o semgrep_result.after.json .
/Users/song-yoonju/.venvs/semgrep/bin/semgrep --config auto .
docker build --check --progress=plain .
```

macOS CA 자동 탐지 오류는 `SSL_CERT_FILE=/etc/ssl/cert.pem`로 해결했다. `auto`는 익명 메트릭을 끄면 설정을 만들 수 없으므로 규칙을 고정한 경우가 아니라면 metrics-off와 함께 사용하지 않아야 한다.

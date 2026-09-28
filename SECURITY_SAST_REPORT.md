# SAST 보안 점검 및 조치 보고서

- 점검일: 2026-09-29
- 작업 브랜치: `security/sast-remediation-20260929`
- 도구: Semgrep 1.178.0, Community `auto` 규칙
- 원본/조치 후 산출물: `semgrep_result.before.json`, `semgrep_result.after.json`

## 1. 결과 요약

| 구분 | 검사 파일 | 실행 규칙 | 검출 건수 |
|---|---:|---:|---:|
| 조치 전 | 94 | 344 | 5 |
| 조치 후 | 101 | 345 | 0 |

초기 5건은 GitHub Actions 가변 참조 4건과 root 컨테이너 1건이었다.

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

## 3. 검증과 트러블슈팅

- Semgrep: 5→0, 종료 코드 0
- Python `compileall`: 통과
- GitHub Actions YAML 파싱: 통과
- Docker `build --check`: 경고 0, 통과
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

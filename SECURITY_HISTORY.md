# BethePet 보안 작업 히스토리

| 순서 | 작업 | 결과 |
|---:|---|---|
| 1 | `security/sast-remediation-20260929`에서 Semgrep 실행 | 초기 5건 확인 |
| 2 | Actions SHA 고정, root 컨테이너 제거, JWT 스택 정비 | 보안 브랜치 Semgrep 0건 |
| 3 | 루트 Poetry 의존성 갱신 및 PyJWT 전환 | 루트 pip-audit 0건 |
| 4 | `develop`과 보안 브랜치의 병합 가능성 분석 | 전체 병합 시 56개 파일·11개 충돌 확인 |
| 5 | 보안 커밋만 `develop`에 선별 병합 | `0187add`, `6ee7b87` 기반 반영 |
| 6 | `develop` 통합 스캔 | 챗봇·Nginx 추가 SAST 5건 발견 |
| 7 | 챗봇 non-root, CORS allowlist, Nginx Upgrade 제한 조치 | 최종 Semgrep 0건 |
| 8 | 챗봇 독립 `poetry.lock` 갱신 및 PyJWT 명시 | 챗봇 pip-audit 0건 |
| 9 | `develop`에 보안·의존성 변경 푸시 | `bbd6e27` |
| 10 | GitHub Dependabot 비동기 재계산 확인 | 106건 → 55건 → 0건 |
| 11 | 최종 SCA 보고서 수치 갱신 | `0827a7a` |
| 12 | CORS preflight 및 전체 병합 충돌 재검토 | 추가 전체 병합하지 않기로 결정 |

## 최종 커밋 흐름

```text
d3ac775  develop 기준점
   └─ 0187add  SAST 조치
      └─ 6ee7b87  루트 의존성·JWT 조치
         └─ bbd6e27  챗봇·Nginx·통합 보안 조치
            └─ 0827a7a  Dependabot 재계산 결과 및 최종 문서
```

전체 보안 브랜치의 `Prod` 및 챗봇 구조 변경은 의도적으로 `develop`에 병합하지 않았다.

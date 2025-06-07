#!/usr/bin/env python3
"""
리포트 API 통합 테스트
pytest로도 실행 가능하고 직접 실행도 가능합니다.

실행 방법:
  # 직접 실행
  python tests/test_api_integration.py

  # pytest로 실행
  pytest tests/test_api_integration.py -v
"""

import json
import os
import sys
from typing import Any, Dict

import pytest
import requests

# 프로젝트 루트 경로 추가 (pytest에서는 자동으로 되지만 직접 실행시 필요)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class ReportAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()  # 쿠키 기반 인증용 세션

    def login(
        self, email: str = "test@bethe.pet", password: str = "testpassword"
    ) -> bool:
        """로그인하여 토큰 획득 (쿠키 기반)"""
        print(f"🔐 로그인 시도: {email}")

        login_data = {
            "email": email,
            "password": password,
        }

        try:
            response = requests.post(
                f"{self.base_url}/user/login",  # 올바른 엔드포인트
                json=login_data,  # JSON으로 전송
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                # 쿠키 기반 인증이므로 세션 사용
                self.session = requests.Session()
                for cookie in response.cookies:
                    self.session.cookies.set(cookie.name, cookie.value)
                print("✅ 로그인 성공! (쿠키 기반 인증)")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 로그인 요청 오류: {e}")
            return False

    def test_comprehensive_report(self, period: str = "week") -> Dict[str, Any]:
        """종합 리포트 테스트"""
        print(f"\n📊 종합 리포트 테스트 (period: {period})")

        try:
            response = self.session.get(
                f"{self.base_url}/report/comprehensive",
                params={"period": period},
            )

            self._print_response("종합 리포트", response)
            return response.json() if response.status_code == 200 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return {}

    def test_health_insight(self, period: str = "week") -> Dict[str, Any]:
        """건강 인사이트 테스트"""
        print(f"\n🧠 건강 인사이트 테스트 (period: {period})")

        try:
            response = self.session.get(
                f"{self.base_url}/report/insight",
                params={"period": period},
            )

            self._print_response("건강 인사이트", response)
            return response.json() if response.status_code == 200 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return {}

    def test_activity_stats(self, period: str = "month") -> Dict[str, Any]:
        """활동 통계 테스트"""
        print(f"\n🏃 활동 통계 테스트 (period: {period})")

        try:
            response = self.session.get(
                f"{self.base_url}/report/activities",
                params={"period": period},
            )

            self._print_response("활동 통계", response)
            return response.json() if response.status_code == 200 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return {}

    def test_health_details(self, period: str = "all") -> Dict[str, Any]:
        """건강 체크 상세 테스트"""
        print(f"\n🩺 건강 체크 상세 테스트 (period: {period})")

        try:
            response = self.session.get(
                f"{self.base_url}/report/health-details",
                params={"period": period},
            )

            self._print_response("건강 체크 상세", response)
            return response.json() if response.status_code == 200 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return {}

    def test_summary(self, period: str = "week") -> Dict[str, Any]:
        """리포트 요약 테스트"""
        print(f"\n📋 리포트 요약 테스트 (period: {period})")

        try:
            response = self.session.get(
                f"{self.base_url}/report/summary",
                params={"period": period},
            )

            self._print_response("리포트 요약", response)
            return response.json() if response.status_code == 200 else {}

        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return {}

    def test_error_cases(self):
        """에러 케이스 테스트"""
        print(f"\n⚠️ 에러 케이스 테스트")

        # 잘못된 period 값
        try:
            response = self.session.get(
                f"{self.base_url}/report/comprehensive",
                params={"period": "invalid"},
            )
            print(f"잘못된 period: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"잘못된 period 테스트 오류: {e}")

        # 인증 없이 요청
        try:
            response = requests.get(f"{self.base_url}/report/summary")
            print(f"인증 없음: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"인증 없음 테스트 오류: {e}")

    def _print_response(self, test_name: str, response: requests.Response):
        """응답 결과 출력"""
        if response.status_code == 200:
            print(f"✅ {test_name} 성공!")
            data = response.json()

            # 주요 정보만 간단히 출력
            if isinstance(data, dict):
                if "health_insight" in data:
                    insight = data["health_insight"]
                    print(f"   건강 점수: {insight.get('score', 'N/A')}점")
                    print(f"   건강 상태: {insight.get('status', 'N/A')}")
                    print(f"   인사이트 개수: {len(insight.get('insights', []))}")

                if "activity_stats" in data:
                    stats = data["activity_stats"]
                    print(f"   산책 횟수: {stats.get('walk_count', 'N/A')}회")
                    print(f"   사료 급여: {stats.get('feed_count', 'N/A')}회")

                if "score" in data:  # insight만 있는 경우
                    print(f"   건강 점수: {data.get('score', 'N/A')}점")
                    print(f"   상태: {data.get('status', 'N/A')}")

                if "walk_count" in data:  # activity stats만 있는 경우
                    print(f"   산책: {data.get('walk_count', 'N/A')}회")
                    print(f"   평균 거리: {data.get('avg_walk_distance', 'N/A')}km")

            elif isinstance(data, list):  # health details
                print(f"   건강 항목 개수: {len(data)}")
                for item in data:
                    print(
                        f"   - {item.get('item', 'N/A')}: {item.get('status', 'N/A')}"
                    )
        else:
            print(f"❌ {test_name} 실패: {response.status_code}")
            print(f"   오류: {response.text[:200]}")

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 리포트 API 테스트 시작")
        print("=" * 50)

        # 로그인
        if not self.login():
            print("❌ 로그인 실패로 테스트 중단")
            return

        # 각 API 테스트
        self.test_comprehensive_report("week")
        self.test_comprehensive_report("month")

        self.test_health_insight("week")
        self.test_activity_stats("month")
        self.test_health_details("all")
        self.test_summary("week")

        # 에러 케이스
        self.test_error_cases()

        print("\n" + "=" * 50)
        print("✅ 모든 테스트 완료!")


# pytest 테스트 클래스
class TestReportAPI:
    """pytest용 테스트 클래스"""

    @pytest.fixture(scope="class")
    def tester(self):
        """테스터 인스턴스 생성"""
        tester = ReportAPITester()
        # 로그인 시도
        if not tester.login():
            pytest.skip("로그인 실패로 테스트 스킵")
        return tester

    def test_server_connection(self):
        """서버 연결 테스트"""
        try:
            response = requests.get("http://localhost:8000/")
            assert response.status_code in [200, 404]  # 서버가 응답하기만 하면 OK
        except requests.exceptions.RequestException:
            pytest.fail("서버에 연결할 수 없습니다")

    def test_comprehensive_report_week(self, tester):
        """주간 종합 리포트 테스트"""
        result = tester.test_comprehensive_report("week")
        assert isinstance(result, dict)
        assert "health_insight" in result
        assert "activity_stats" in result

    def test_health_insight(self, tester):
        """건강 인사이트 테스트"""
        result = tester.test_health_insight("week")
        assert isinstance(result, dict)
        assert "score" in result
        assert "status" in result
        assert isinstance(result.get("score"), int)

    def test_activity_stats(self, tester):
        """활동 통계 테스트"""
        result = tester.test_activity_stats("month")
        assert isinstance(result, dict)
        assert "walk_count" in result
        assert "feed_count" in result


def main():
    """메인 실행 함수 - 직접 실행시"""
    print("🧪 리포트 API 통합 테스트")
    print("FastAPI 서버가 실행 중인지 확인하세요!")
    print()

    # 서버 연결 테스트
    try:
        response = requests.get("http://localhost:8000/")
        print("✅ 서버 연결 확인")
    except requests.exceptions.RequestException:
        print("❌ 서버에 연결할 수 없습니다. FastAPI 서버를 먼저 실행하세요.")
        print("   uvicorn api.main:app --reload")
        return

    # 테스트 실행
    tester = ReportAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()

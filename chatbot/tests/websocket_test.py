import asyncio
import json
import uuid

import websockets


async def test_chatbot():
    # 테스트용 쿠키 (실제 로그인해서 얻은 access_token으로 교체 필요)


    # 웹소켓 연결 설정
    websocket_url = "ws://localhost/ws"
    headers = {"Cookie": cookie}

    print("\n=== 상황 1: 식욕부진 관련 대화 (대화형 모드 테스트) ===")
    async with websockets.connect(
        websocket_url,
        extra_headers=headers,
        ping_interval=30,
        ping_timeout=15,
    ) as websocket:
        # 1. 새 대화방 생성
        await websocket.send(
            json.dumps({"type": "create_room", "payload": {"title": ""}})
        )
        response = await websocket.recv()
        room_data = json.loads(response)
        room_id = room_data["payload"]["id"]
        print("\n대화방 생성 응답:", room_data)

        # 2. 첫 메시지 전송 (식욕부진 관련)
        await websocket.send(
            json.dumps(
                {
                    "type": "send_first_message",
                    "payload": {
                        "room_id": room_id,
                        "content": "우리 애가 자꾸 어제부터 입맛이 없고 물도 안마셔요",
                    },
                }
            )
        )
        response = await websocket.recv()
        response_data = json.loads(response)
        print("\n첫 메시지 AI 응답:", response_data)

        # chat_state 확인
        assert (
            response_data["payload"]["chat_state"] == "waiting_for_additional"
        ), "첫 메시지 후 chat_state가 waiting_for_additional이어야 함"
        print("✅ chat_state 확인: waiting_for_additional")

        # 3. 추가 증상 없음 응답
        await websocket.send(
            json.dumps(
                {
                    "type": "send_message",
                    "payload": {"room_id": room_id, "content": "없음"},
                }
            )
        )
        response = await websocket.recv()
        response_data = json.loads(response)
        print("\n'없음' 응답에 대한 AI 답변:", response_data)

        # chat_state 확인
        assert (
            response_data["payload"]["chat_state"] == "initial"
        ), "'없음' 응답 후 chat_state가 initial이어야 함"
        print("✅ chat_state 확인: initial")

    print("\n=== 상황 2: 공격성 관련 대화 (추가 증상 있는 경우) ===")
    async with websockets.connect(
        websocket_url,
        extra_headers=headers,
        ping_interval=30,
        ping_timeout=15,
    ) as websocket:
        # 1. 새 대화방 생성
        await websocket.send(
            json.dumps({"type": "create_room", "payload": {"title": ""}})
        )
        response = await websocket.recv()
        room_data = json.loads(response)
        room_id = room_data["payload"]["id"]
        print("\n두 번째 대화방 생성 응답:", room_data)

        # 2. 첫 메시지 전송 (공격성 관련)
        await websocket.send(
            json.dumps(
                {
                    "type": "send_first_message",
                    "payload": {
                        "room_id": room_id,
                        "content": "우리 강아지가 다른 강아지를 보면 짖고 공격적이에요",
                    },
                }
            )
        )
        response = await websocket.recv()
        response_data = json.loads(response)
        print("\n공격성 관련 AI 응답:", response_data)

        # chat_state 확인
        assert (
            response_data["payload"]["chat_state"] == "waiting_for_additional"
        ), "첫 메시지 후 chat_state가 waiting_for_additional이어야 함"
        print("✅ chat_state 확인: waiting_for_additional")

        # 3. 추가 증상 입력
        await websocket.send(
            json.dumps(
                {
                    "type": "send_message",
                    "payload": {
                        "room_id": room_id,
                        "content": "그리고 평소보다 식욕이 줄었어요",
                    },
                }
            )
        )
        response = await websocket.recv()
        response_data = json.loads(response)
        print("\n추가 증상 입력에 대한 AI 답변:", response_data)

        # chat_state 확인
        assert (
            response_data["payload"]["chat_state"] == "initial"
        ), "추가 증상 입력 후 chat_state가 initial이어야 함"
        print("✅ chat_state 확인: initial")

    print("\n=== 상황 3: 대화방 삭제 시 상태 초기화 테스트 ===")
    async with websockets.connect(
        websocket_url,
        extra_headers=headers,
        ping_interval=30,
        ping_timeout=15,
    ) as websocket:
        # 1. 새 대화방 생성
        await websocket.send(
            json.dumps({"type": "create_room", "payload": {"title": ""}})
        )
        response = await websocket.recv()
        room_data = json.loads(response)
        room_id = room_data["payload"]["id"]

        # 2. 첫 메시지 전송
        await websocket.send(
            json.dumps(
                {
                    "type": "send_first_message",
                    "payload": {
                        "room_id": room_id,
                        "content": "우리 강아지가 기침을 해요",
                    },
                }
            )
        )
        response = await websocket.recv()
        response_data = json.loads(response)

        # chat_state 확인
        assert (
            response_data["payload"]["chat_state"] == "waiting_for_additional"
        ), "첫 메시지 후 chat_state가 waiting_for_additional이어야 함"
        print("✅ chat_state 확인: waiting_for_additional")

        # 3. 대화방 삭제
        await websocket.send(
            json.dumps({"type": "delete_room", "payload": {"room_id": room_id}})
        )
        response = await websocket.recv()
        print("\n대화방 삭제 응답:", json.loads(response))

        # 4. 삭제된 대화방에 메시지 전송 시도 (에러 확인)
        try:
            await websocket.send(
                json.dumps(
                    {
                        "type": "send_message",
                        "payload": {
                            "room_id": room_id,
                            "content": "추가 증상이 있어요",
                        },
                    }
                )
            )
            response = await websocket.recv()
            response_data = json.loads(response)
            assert (
                response_data["type"] == "error"
            ), "삭제된 대화방에 메시지 전송 시 에러가 발생해야 함"
            print("✅ 삭제된 대화방 메시지 전송 에러 확인")
        except Exception as e:
            print(f"✅ 예상된 에러 발생: {str(e)}")

    print("\n=== 모든 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_chatbot())

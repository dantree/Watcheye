from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # 받은 메시지를 클라이언트로 에코합니다.
            await websocket.send_text(f"메시지 받았습니다: {data}")
    except WebSocketDisconnect:
        print("클라이언트 연결 종료") 
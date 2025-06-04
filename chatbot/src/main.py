import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .websocket.router import router as websocket_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BethePet Chatbot Service",
    description="WebSocket based chatbot service for pet healthcare",
    version="1.0.0",
)

# CORS 설정
origins = [
    "http://localhost",
    "http://localhost:3000",  # React 프론트엔드
    "http://localhost:8000",  # API 서비스
    "https://yoon.today",  # 프로덕션 프론트엔드
    "https://api.yoon.today",  # 프로덕션 백엔드
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 라우터 추가
app.include_router(websocket_router, prefix="/chat", tags=["chat"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the chatbot service
    """
    return {"status": "healthy", "service": "chatbot"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8001)), reload=True
    )

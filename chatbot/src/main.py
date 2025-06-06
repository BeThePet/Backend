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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 웹소켓 라우터 등록
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Welcome to BethePet Chatbot Service"}


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

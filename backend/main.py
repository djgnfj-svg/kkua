from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.postgres import Base, engine
from routers import postgres_rooms, guests, gamerooms, gamerounds, gameresults

app = FastAPI(title="게임방 관리 API", description="PostgreSQL을 사용한 게임방 및 게임 관리 API")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 실제 프론트엔드 도메인으로 제한하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(postgres_rooms.router)
app.include_router(guests.router)
app.include_router(gamerooms.router)
app.include_router(gamerounds.router)
app.include_router(gameresults.router)

@app.get("/")
async def root():
    return {"message": "게임방 관리 API에 오신 것을 환영합니다!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
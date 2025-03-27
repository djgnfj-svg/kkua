from fastapi import FastAPI
from routers import postgres_rooms

app = FastAPI(title="게임방 관리 API", description="PostgreSQL을 사용한 게임방 관리 API")

# 라우터 등록
app.include_router(postgres_rooms.router)

@app.get("/")
async def root():
    return {"message": "게임방 관리 API에 오신 것을 환영합니다!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
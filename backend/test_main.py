import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, Base, Room, SessionLocal

# SQLite 인메모리 DB 설정
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

import main
main.SessionLocal = TestingSessionLocal
app.dependency_overrides[SessionLocal] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_room():
    # 방 생성 테스트
    response = client.post(
        "/rooms",
        json={"title": "테스트 방", "room_type": "일반", "max_people": 4}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "테스트 방"
    assert data["people"] == 1
    assert data["room_type"] == "일반"
    assert data["max_people"] == 4
    assert data["playing"] == False

def test_read_rooms():
    # 방 목록 조회 테스트
    client.post("/rooms", json={"title": "방1", "room_type": "일반"})
    client.post("/rooms", json={"title": "방2", "room_type": "스피드"})
    
    response = client.get("/rooms")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "방1"
    assert data[1]["title"] == "방2"

def test_read_room():
    # 단일 방 조회 테스트
    create_response = client.post("/rooms", json={"title": "단일 방", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "단일 방"
    assert data["room_type"] == "일반"
    assert "id" in data

def test_update_room():
    # 방 정보 수정 테스트
    create_response = client.post("/rooms", json={"title": "수정 전", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    response = client.put(
        f"/rooms/{room_id}",
        json={"title": "수정 후"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "수정 후"
    assert data["room_type"] == "일반"
    
    response = client.put(
        f"/rooms/{room_id}",
        json={"title": "다시 수정", "room_type": "스피드"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "다시 수정"
    assert data["room_type"] == "일반"

def test_delete_room():
    # 방 삭제 테스트
    create_response = client.post("/rooms", json={"title": "삭제할 방", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    response = client.delete(f"/rooms/{room_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "방이 성공적으로 삭제되었습니다"
    
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 404

def test_join_and_leave_room():
    # 방 참여/퇴장 테스트
    create_response = client.post("/rooms", json={"title": "참여 테스트", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 2
    
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 3
    
    response = client.post(f"/rooms/{room_id}/leave")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 2

def test_room_max_capacity():
    # 방 최대 인원 제한 테스트
    create_response = client.post(
        "/rooms", 
        json={"title": "인원제한 테스트", "room_type": "일반", "max_people": 3}
    )
    room_id = create_response.json()["id"]
    
    for _ in range(2):
        response = client.post(f"/rooms/{room_id}/join")
        assert response.status_code == 200
    
    response = client.get(f"/rooms/{room_id}")
    assert response.json()["people"] == 3
    
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 400
    assert "가득 찼습니다" in response.json()["detail"]

def test_auto_delete_empty_room():
    # 빈 방 자동 삭제 테스트
    create_response = client.post("/rooms", json={"title": "빈 방 테스트", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    join_response = client.post(f"/rooms/{room_id}/join")
    assert join_response.status_code == 200
    assert join_response.json()["people"] == 2
    
    leave_response = client.post(f"/rooms/{room_id}/leave")
    assert leave_response.status_code == 200
    assert leave_response.json()["people"] == 1
    
    leave_response = client.post(f"/rooms/{room_id}/leave")
    assert leave_response.status_code == 200
    assert "자동으로 삭제되었습니다" in leave_response.json()["message"]
    
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404

def test_game_play_status():
    # 게임 상태 변경 테스트
    create_response = client.post("/rooms", json={"title": "게임방", "room_type": "일반"})
    room_id = create_response.json()["id"]
    
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == False
    
    play_response = client.post(f"/rooms/{room_id}/play")
    assert play_response.status_code == 200
    assert play_response.json()["playing"] == True
    
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == True
    
    end_response = client.post(f"/rooms/{room_id}/end")
    assert end_response.status_code == 200
    assert end_response.json()["playing"] == False
    
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == False

def test_nonexistent_room():
    # 존재하지 않는 방 접근 테스트
    room_id = 9999
    
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404
    
    put_response = client.put(f"/rooms/{room_id}", json={"title": "변경 시도"})
    assert put_response.status_code == 404
    
    delete_response = client.delete(f"/rooms/{room_id}")
    assert delete_response.status_code == 404
    
    join_response = client.post(f"/rooms/{room_id}/join")
    assert join_response.status_code == 404
    
    leave_response = client.post(f"/rooms/{room_id}/leave")
    assert leave_response.status_code == 404
    
    play_response = client.post(f"/rooms/{room_id}/play")
    assert play_response.status_code == 404
    
    end_response = client.post(f"/rooms/{room_id}/end")
    assert end_response.status_code == 404

def test_input_validation():
    # 입력값 유효성 검사 테스트
    response = client.post("/rooms", json={"title": "", "room_type": "일반"})
    assert response.status_code == 422
    
    response = client.post("/rooms", json={"title": "타입 없음"})
    assert response.status_code == 422
    
    response = client.post("/rooms", data="유효하지 않은 JSON")
    assert response.status_code == 422
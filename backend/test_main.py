import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, Base, Room, SessionLocal

# 테스트용 인메모리 DB 설정
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 의존성 오버라이드를 위한 설정
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 의존성 오버라이드 적용
import main
main.SessionLocal = TestingSessionLocal
app.dependency_overrides[SessionLocal] = override_get_db

# 테스트 클라이언트 설정
client = TestClient(app)

# 테스트 실행 전 데이터베이스 초기화
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# API 테스트 코드
def test_create_room():
    response = client.post(
        "/rooms",
        json={"title": "테스트 방", "level": "초급"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "테스트 방"
    assert data["people"] == 1
    assert data["level"] == "초급"
    assert data["playing"] == False

def test_read_rooms():
    # 먼저 방 생성
    client.post("/rooms", json={"title": "방1", "level": "중급"})
    client.post("/rooms", json={"title": "방2", "level": "고급"})
    
    # 방 목록 조회
    response = client.get("/rooms")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "방1"
    assert data[1]["title"] == "방2"

def test_read_room():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "단일 방", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 단일 방 조회
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "단일 방"
    assert data["level"] == "초급"
    assert "id" in data

def test_update_room():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "수정 전", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 방 제목만 수정
    response = client.put(
        f"/rooms/{room_id}",
        json={"title": "수정 후"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "수정 후"
    assert data["level"] == "초급"
    
    # level 필드가 있어도 무시됨
    response = client.put(
        f"/rooms/{room_id}",
        json={"title": "다시 수정", "level": "고급"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "다시 수정"
    assert data["level"] == "초급"

def test_delete_room():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "삭제할 방", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 방 삭제
    response = client.delete(f"/rooms/{room_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "방이 성공적으로 삭제되었습니다"
    
    # 삭제된 방 조회 시도
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 404

def test_join_and_leave_room():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "참여 테스트", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 방 참여
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 2
    
    # 한 명 더 참여
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 3
    
    # 참여 취소
    response = client.post(f"/rooms/{room_id}/leave")
    assert response.status_code == 200
    data = response.json()
    assert data["people"] == 2

def test_room_max_capacity():
    # 방 생성 (생성자 1명)
    create_response = client.post("/rooms", json={"title": "인원제한 테스트", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 3명 더 참여 (총 4명)
    for _ in range(3):
        response = client.post(f"/rooms/{room_id}/join")
        assert response.status_code == 200
    
    # 최대 인원 확인
    response = client.get(f"/rooms/{room_id}")
    assert response.json()["people"] == 4
    
    # 5번째 참여 시도 - 실패해야 함
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 400
    assert "가득 찼습니다" in response.json()["detail"]

def test_auto_delete_empty_room():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "빈 방 테스트", "level": "초급"})
    room_id = create_response.json()["id"]
    
    # 방 참여
    join_response = client.post(f"/rooms/{room_id}/join")
    assert join_response.status_code == 200
    assert join_response.json()["people"] == 2
    
    # 두 참여자가 모두 나가면 방이 자동으로 삭제되어야 함
    leave_response = client.post(f"/rooms/{room_id}/leave")  # 첫 번째 퇴장
    assert leave_response.status_code == 200
    assert leave_response.json()["people"] == 1
    
    leave_response = client.post(f"/rooms/{room_id}/leave")  # 두 번째 퇴장
    assert leave_response.status_code == 200
    assert "자동으로 삭제되었습니다" in leave_response.json()["message"]
    
    # 삭제된 방 조회 시도
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404

def test_game_play_status():
    # 방 생성
    create_response = client.post("/rooms", json={"title": "게임방", "level": "중급"})
    room_id = create_response.json()["id"]
    
    # 초기 상태 확인 (플레이 중 아님)
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == False
    
    # 게임 시작
    play_response = client.post(f"/rooms/{room_id}/play")
    assert play_response.status_code == 200
    assert play_response.json()["playing"] == True
    
    # 상태 확인 (플레이 중)
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == True
    
    # 게임 종료
    end_response = client.post(f"/rooms/{room_id}/end")
    assert end_response.status_code == 200
    assert end_response.json()["playing"] == False
    
    # 상태 확인 (플레이 중 아님)
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.json()["playing"] == False

def test_nonexistent_room():
    # 존재하지 않는 방 ID (예: 9999)로 요청
    room_id = 9999
    
    # 조회 시도
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404
    
    # 업데이트 시도
    put_response = client.put(f"/rooms/{room_id}", json={"title": "변경 시도"})
    assert put_response.status_code == 404
    
    # 삭제 시도
    delete_response = client.delete(f"/rooms/{room_id}")
    assert delete_response.status_code == 404
    
    # 참여 시도
    join_response = client.post(f"/rooms/{room_id}/join")
    assert join_response.status_code == 404
    
    # 퇴장 시도
    leave_response = client.post(f"/rooms/{room_id}/leave")
    assert leave_response.status_code == 404
    
    # 게임 시작 시도
    play_response = client.post(f"/rooms/{room_id}/play")
    assert play_response.status_code == 404
    
    # 게임 종료 시도
    end_response = client.post(f"/rooms/{room_id}/end")
    assert end_response.status_code == 404

def test_input_validation():
    # 빈 제목으로 방 생성 시도
    response = client.post("/rooms", json={"title": "", "level": "초급"})
    assert response.status_code == 422  # FastAPI의 기본 검증 오류 코드
    
    # 레벨 누락으로 방 생성 시도
    response = client.post("/rooms", json={"title": "레벨 없음"})
    assert response.status_code == 422
    
    # 유효하지 않은 JSON 형식으로 방 생성 시도
    response = client.post("/rooms", data="유효하지 않은 JSON")
    assert response.status_code == 422
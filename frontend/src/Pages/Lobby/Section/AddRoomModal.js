import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { gameLobbyUrl, gameUrl } from '../../../Component/urls';
import guestStore from '../../../store/guestStore';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
    const navigate = useNavigate();
  
    const [makeRoom, setMakeRoom] = useState({
        title: "",
        game_mode: "arcade",
        max_players: 2,
        time_limit: 120,
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmitBtn = async () => {
        const { title, max_players, game_mode, time_limit } = makeRoom;

        if (isSubmitting) return;
        if (title.trim().length < 2) {
            alert("방 제목은 최소 2자 이상 입력해주세요.");
            return;
        }

        try {
            setIsSubmitting(true);
            const res = await axiosInstance.post(
                `${ROOM_API.CREATE_ROOMS}?title=${title}&max_players=${max_players}&game_mode=${game_mode}&time_limit=${time_limit}`
            );
            navigate(`${gameLobbyUrl(res.data.room_id)}`);
        } catch (error) {
            if (!error.response) {
                alert("네트워크 오류입니다. 연결을 확인해주세요.");
            } else if (error.response.status === 403) {
                alert("인증이 만료되었습니다. 다시 접속해주세요.");
                guestStore.getState().clearGuestInfo();
                navigate("/");
            } else if (error.response.status === 400) {
                alert("이미 플레이중인 게임이 존재합니다.");
            } else {
                alert("방 생성에 실패했습니다. 다시 시도해주세요.");
            }
            console.log(error);
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="modal-app">
            <Modal
                isOpen={isOpen}
                onRequestClose={() => isClose(false)}
                contentLabel="Add Room Modal"
                style={{
                    overlay: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
                    content: { border: 'none', background: 'none', padding: 0 }
                }}>
                <div className="modal-container">
                    <div className="modal-ears">
                        <div className="ear left"></div>
                        <div className="ear right"></div>
                    </div>
                    <div className="modal-content">
                        <button className="close-btn" onClick={() => isClose(false)}>×</button>
                        <h2 className="modal-title">끄아 방 만들기</h2>

                        {/* 방 제목 입력 */}
                        <input
                            type="text"
                            placeholder="방 제목 (최대 10자)"
                            value={makeRoom.title}
                            onChange={(e) =>
                                setMakeRoom({ ...makeRoom, title: e.target.value.slice(0, 10) })
                            }
                            className="room-title-input"
                        />

                        {/* 게임 설정 */}
                        <div className="game-settings">
                            <div className="game-mode-section">
                                <div className="label">게임 모드</div>
                                <div className="mode-buttons">
                                    <button
                                        className={`mode-btn active`}
                                        onClick={() => setMakeRoom({ ...makeRoom, game_mode: 'arcade' })}
                                    >
                                        아케이드
                                    </button>
                                    <button
                                        className={`mode-btn boss`}
                                        onClick={() => alert("wating for Update v0.2 ~")}
                                    >
                                        보스전
                                    </button>
                                </div>
                            </div>

                            <div className="game-size-section">
                                <div className="label">인원</div>
                                <div className="size-buttons">
                                    {[2, 3, 4].map((num) => (
                                        <label key={num}>
                                            <input
                                                type="radio"
                                                name="size"
                                                value={num}
                                                checked={makeRoom.max_players === num}
                                                onChange={() => setMakeRoom({ ...makeRoom, max_players: num })}
                                            />{' '}
                                            {num}인
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* 생성 및 취소 버튼 */}
                        <div className="create-btn-wrapper">
                          <button
                            className={makeRoom.title.length >= 2 && makeRoom.game_mode !== "" && !isSubmitting ? 'create-btn' : 'create-btn-fasle'}
                            onClick={handleSubmitBtn}
                            disabled={makeRoom.title.length >= 2 && makeRoom.game_mode !== "" && !isSubmitting ? false : true}
                          >
                            생성하기
                          </button>
                          <button
                            className="cancel-btn"
                            onClick={() => isClose(false)}
                          >
                            취소하기
                          </button>
                        </div>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default AddRoomModal;

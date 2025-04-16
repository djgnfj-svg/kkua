import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { gameLobbyUrl, gameUrl } from '../../../Component/urls';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
    const navigate = useNavigate();
  
    const [makeRoom, setMakeRoom] = useState({
        title: "",
        game_mode: "arcade",
        max_players:2,
        time_limit:120,
    });

    const handleSubmitBtn = async () => {
        const {title , max_players , game_mode , time_limit} = makeRoom
        try {
            const res = await axiosInstance.post(
                `${ROOM_API.CREATE_ROOMS}?title=${title}&max_players=${max_players}&game_mode=${game_mode}&time_limit=${time_limit}`
            );
            navigate(`${gameLobbyUrl(res.data.room_id)}`);
        }
        catch (error) {
            console.log(error);
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
                            placeholder="방 제목"
                            value={makeRoom.title}
                            onChange={(e) =>
                                setMakeRoom({ ...makeRoom, title: e.target.value })
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
                                        onClick={() => setMakeRoom({ ...makeRoom, mode: 'arcade' })}
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

                        {/* 생성 버튼 */}
                        <button
                            className={makeRoom.title.length >= 2 && makeRoom.mode !== "" ? 'create-btn' : 'create-btn-fasle'}
                            onClick={handleSubmitBtn}
                            disabled={makeRoom.title.length >= 2 && makeRoom.mode !== "" ? false : true}
                        >
                            생성하기
                        </button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default AddRoomModal;

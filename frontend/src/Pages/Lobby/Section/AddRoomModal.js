import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { useNavigate } from 'react-router-dom';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
    const navigate = useNavigate();
  
    const [makeRoom, setMakeRoom] = useState({
        roomTitle: "",
        mode: "",
        people: ""
    });

    const handleSubmitBtn = async () => {
        try {
            const res = await axiosInstance.post(ROOM_API.CREATE_ROOMS,{
                roomTitle:makeRoom.roomTitle,
                mode : makeRoom.mode,
                people : makeRoom.people
            })
            console.log(res.data);
            navigate("/kea");
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
                            value={makeRoom.roomTitle}
                            onChange={(e) =>
                                setMakeRoom({ ...makeRoom, roomTitle: e.target.value })
                            }
                            className="room-title-input"
                        />

                        {/* 게임 설정 */}
                        <div className="game-settings">
                            <div className="game-mode-section">
                                <div className="label">게임 모드</div>
                                <div className="mode-buttons">
                                    <button
                                        className={`mode-btn ${makeRoom.mode === 'arcade' ? 'active' : ''}`}
                                        onClick={() => setMakeRoom({ ...makeRoom, mode: 'arcade' })}
                                    >
                                        아케이드
                                    </button>
                                    <button
                                        className={`mode-btn ${makeRoom.mode === 'boss' ? 'active' : ''}`}
                                        onClick={() => setMakeRoom({ ...makeRoom, mode: 'boss' })}
                                    >
                                        보스전
                                    </button>
                                </div>
                            </div>

                            <div className="game-size-section">
                                <div className="label">인원</div>
                                <div className="size-buttons">
                                    {['2', '3', '4'].map((num) => (
                                        <label key={num}>
                                            <input
                                                type="radio"
                                                name="size"
                                                value={num}
                                                checked={makeRoom.people === num}
                                                onChange={() => setMakeRoom({ ...makeRoom, people: num })}
                                            />{' '}
                                            {num}인
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* 생성 버튼 */}
                        <button
                            className={makeRoom.roomTitle.length >= 2 ? 'create-btn' : 'create-btn-fasle'}
                            onClick={handleSubmitBtn}
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

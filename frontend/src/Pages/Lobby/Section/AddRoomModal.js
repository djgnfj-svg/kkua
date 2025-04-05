import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
<<<<<<< HEAD
=======
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { useNavigate } from 'react-router-dom';
>>>>>>> 398cbea51763d6c68cc2a501273f879b9fb37e9d

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
<<<<<<< HEAD
    const [roomTitle, setRoomTitle] = useState('');
=======
    const navigate = useNavigate();
  
    const [makeRoom, setMakeRoom] = useState({
        title: "",
        mode: "",
        people: ""
    });

    const handleSubmitBtn = async () => {
        try {
            const res = await axiosInstance.post(ROOM_API.CREATE_ROOMS,{
                title:makeRoom.title,
                room_type : "string",
                max_people : makeRoom.people
            })
            navigate("/kea");
        }
        catch (error) {
            console.log(error);
        }
    }
>>>>>>> 398cbea51763d6c68cc2a501273f879b9fb37e9d

    return (
        <div className="modal-app">
            <Modal
                isOpen={isOpen}
                onRequestClose={() => isClose(false)}
                contentLabel="Add Room Modal"
                style={{
                    overlay: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
                    content: { border: 'none', background: 'none', padding: 0 }
<<<<<<< HEAD
                }}
            >
=======
                }}>
>>>>>>> 398cbea51763d6c68cc2a501273f879b9fb37e9d
                <div className="modal-container">
                    <div className="modal-ears">
                        <div className="ear left"></div>
                        <div className="ear right"></div>
                    </div>
                    <div className="modal-content">
                        <button className="close-btn" onClick={() => isClose(false)}>×</button>
                        <h2 className="modal-title">끄아 방 만들기</h2>
<<<<<<< HEAD
                        <input 
                            type="text" 
                            placeholder="방 제목" 
                            value={roomTitle} 
                            onChange={(e) => setRoomTitle(e.target.value)}
                            className="room-title-input"
                        />
                        <button className="create-btn">생성하기</button>
=======

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
                            className={makeRoom.title.length >= 2 && makeRoom.mode !== "" && makeRoom.people !== "" ? 'create-btn' : 'create-btn-fasle'}
                            onClick={handleSubmitBtn} disabled={makeRoom.title.length >= 2 && makeRoom.mode !== "" && makeRoom.people !== "" ? false : true}
                        >
                            생성하기
                        </button>
>>>>>>> 398cbea51763d6c68cc2a501273f879b9fb37e9d
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default AddRoomModal;

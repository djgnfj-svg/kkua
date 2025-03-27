import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { useNavigate } from 'react-router-dom';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
    const navigate = useNavigate();
    const [roomTitle, setRoomTitle] = useState('');

    const handleSubmitBtn = async () => {
        try {
            const res = await axiosInstance.post(ROOM_API.CREATE_ROOMS);
            console.log(res.data);
            navigate("/kea");
        }
        catch (error) {
            console.log(error)
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
                        <input
                            type="text"
                            placeholder="방 제목"
                            value={roomTitle}
                            onChange={(e) => setRoomTitle(e.target.value)}
                            className="room-title-input" />
                        <button className="create-btn" onClick={() => handleSubmitBtn()}>생성하기</button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default AddRoomModal;

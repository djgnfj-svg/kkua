import React, { useState } from 'react';
import Modal from 'react-modal';
import './AddRoomModal.css';

Modal.setAppElement('#root');

function AddRoomModal({ isOpen, isClose }) {
    const [roomTitle, setRoomTitle] = useState('');

    return (
        <div className="modal-app">
            <Modal
                isOpen={isOpen}
                onRequestClose={() => isClose(false)}
                contentLabel="Add Room Modal"
                style={{
                    overlay: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
                    content: { border: 'none', background: 'none', padding: 0 }
                }}
            >
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
                            className="room-title-input"
                        />
                        <button className="create-btn">생성하기</button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}

export default AddRoomModal;

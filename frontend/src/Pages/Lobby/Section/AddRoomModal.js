import React, { useEffect, useState } from 'react'
import Modal from 'react-modal';

Modal.setAppElement('#root');

function AddRoomModal( {isOpen , isClose} ) {
    
    return (
        <div className="Modal_App">
            <Modal
                isOpen={isOpen}            // 모달 상태
                onRequestClose={() => isClose(false)}  // 닫기 설정 (ESC 키나 배경 클릭 시 닫힘)
                contentLabel="Example Modal"    // 접근성 향상을 위한 레이블
                style={{
                    overlay: { backgroundColor: 'rgba(0, 0, 0, 0.5)' }, // 모달 배경
                    content: {
                         width: '300px', height: '300px', margin: 'auto'
                        } // 모달 본문 스타일
                }}
            >
                <h2></h2>
                <p>이곳은 모달 내용입니다.</p>
                <button onClick={() => isClose(false)}>
                    닫기
                </button>
            </Modal>
        </div>
    )
}

export default AddRoomModal



import React from 'react'; 

function LoadingButton({ text, id, onClick }) {
    return (
        <button
            id={id}
            className="mt-5 w-[80%] max-w-[302px] h-[16vw] max-h-[78px] border border-[#9f9f9f] rounded-full bg-white text-black text-[25px] shadow-[0_4px_5px_rgba(0,0,0,0.25)] hover:bg-gray-100 transition"
            onClick={onClick}>
            {text}
        
        </button>
    )
}

export default LoadingButton; 
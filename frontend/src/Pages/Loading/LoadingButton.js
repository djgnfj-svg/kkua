import React from 'react';

function LoadingButton({ text, id, onClick, loading = false, disabled = false }) {
  return (
    <button
      id={id}
      className={`mt-5 w-[80%] max-w-[302px] h-[16vw] max-h-[78px] border border-[#9f9f9f] rounded-full bg-white text-black text-[25px] shadow-[0_4px_5px_rgba(0,0,0,0.25)] transition relative ${
        disabled || loading 
          ? 'opacity-50 cursor-not-allowed' 
          : 'hover:bg-gray-100 active:bg-gray-200'
      }`}
      onClick={loading || disabled ? undefined : onClick}
      disabled={loading || disabled}
    >
      {loading ? (
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-gray-600 mr-2"></div>
          처리중...
        </div>
      ) : (
        text
      )}
    </button>
  );
}

export default LoadingButton;

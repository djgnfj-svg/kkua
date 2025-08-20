import React from 'react';
import toast, { Toaster } from 'react-hot-toast';
// import type { Toast as HotToast } from 'react-hot-toast';

// Toast 유틸리티 함수들
export const showToast = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  loading: (message: string) => toast.loading(message),
  info: (message: string) => toast(message, { icon: '📢' }),
  warning: (message: string) => toast(message, { icon: '⚠️' }),
  game: (message: string) => toast(message, { icon: '🎮' }),
  dismiss: (toastId?: string) => toast.dismiss(toastId),
  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: Error) => string);
    }
  ) => toast.promise(promise, messages)
};

// 커스텀 토스트 컴포넌트 (사용 안함)
/*
const CustomToast: React.FC<{ t: HotToast }> = ({ t }) => (
  <div
    className={`${
      t.visible ? 'animate-enter' : 'animate-leave'
    } max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
  >
    <div className="flex-1 w-0 p-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {t.type === 'success' && (
            <div className="w-5 h-5 text-green-400">✓</div>
          )}
          {t.type === 'error' && (
            <div className="w-5 h-5 text-red-400">✗</div>
          )}
          {t.type === 'loading' && (
            <div className="w-5 h-5 text-blue-400 animate-spin">⟳</div>
          )}
          {!['success', 'error', 'loading'].includes(t.type) && t.icon && (
            <div className="w-5 h-5">{t.icon}</div>
          )}
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-gray-900">
            {typeof t.message === 'string' ? t.message : ''}
          </p>
        </div>
      </div>
    </div>
    <div className="flex border-l border-gray-200">
      <button
        onClick={() => toast.dismiss(t.id)}
        className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-600 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        ✕
      </button>
    </div>
  </div>
);
*/

// 토스터 래퍼 컴포넌트
export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
      gutter={8}
      containerClassName=""
      containerStyle={{}}
      toastOptions={{
        className: '',
        duration: 4000,
        style: {
          background: 'transparent',
          boxShadow: 'none',
          padding: 0,
          margin: 0,
        },
      }}
    />
  );
};

export default ToastProvider;
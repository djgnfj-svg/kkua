import { create } from 'zustand';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

export interface Modal {
  id: string;
  type: string;
  title?: string;
  content?: React.ReactNode;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
}

interface UiState {
  // 로딩 상태
  isLoading: boolean;
  loadingMessage?: string;
  
  // 토스트
  toasts: Toast[];
  
  // 모달
  modals: Modal[];
  
  // 사이드바/메뉴
  isSidebarOpen: boolean;
  
  // 전역 설정
  theme: 'light' | 'dark';
  soundEnabled: boolean;
  
  // Actions
  setLoading: (loading: boolean, message?: string) => void;
  
  // Toast actions
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
  
  // Modal actions
  openModal: (modal: Omit<Modal, 'id'>) => void;
  closeModal: (id: string) => void;
  closeAllModals: () => void;
  
  // UI actions
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  
  // Settings
  setTheme: (theme: 'light' | 'dark') => void;
  setSoundEnabled: (enabled: boolean) => void;
}

export const useUiStore = create<UiState>((set, get) => ({
  // Initial state
  isLoading: false,
  loadingMessage: undefined,
  toasts: [],
  modals: [],
  isSidebarOpen: false,
  theme: 'light',
  soundEnabled: true,
  
  // Loading actions
  setLoading: (loading, message) => set({ 
    isLoading: loading, 
    loadingMessage: loading ? message : undefined 
  }),
  
  // Toast actions
  addToast: (toast) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { ...toast, id };
    
    set((state) => ({
      toasts: [...state.toasts, newToast]
    }));
    
    // 자동 제거 (기본 5초)
    const duration = toast.duration || 5000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }
  },
  
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter(toast => toast.id !== id)
  })),
  
  clearToasts: () => set({ toasts: [] }),
  
  // Modal actions
  openModal: (modal) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newModal = { ...modal, id };
    
    set((state) => ({
      modals: [...state.modals, newModal]
    }));
  },
  
  closeModal: (id) => set((state) => ({
    modals: state.modals.filter(modal => modal.id !== id)
  })),
  
  closeAllModals: () => set({ modals: [] }),
  
  // UI actions
  toggleSidebar: () => set((state) => ({ 
    isSidebarOpen: !state.isSidebarOpen 
  })),
  
  setSidebar: (open) => set({ isSidebarOpen: open }),
  
  // Settings
  setTheme: (theme) => {
    set({ theme });
    // 로컬스토리지에 저장
    localStorage.setItem('theme', theme);
    // HTML에 클래스 적용
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  },
  
  setSoundEnabled: (enabled) => {
    set({ soundEnabled: enabled });
    localStorage.setItem('soundEnabled', enabled.toString());
  }
}));

// 편의 함수들
export const useLoading = () => {
  const { isLoading, loadingMessage, setLoading } = useUiStore();
  return { isLoading, loadingMessage, setLoading };
};

export const useToast = () => {
  const { toasts, addToast, removeToast, clearToasts } = useUiStore();
  
  const toast = {
    success: (message: string, duration?: number) => 
      addToast({ type: 'success', message, duration }),
    error: (message: string, duration?: number) => 
      addToast({ type: 'error', message, duration }),
    info: (message: string, duration?: number) => 
      addToast({ type: 'info', message, duration }),
    warning: (message: string, duration?: number) => 
      addToast({ type: 'warning', message, duration }),
  };
  
  return { toasts, toast, removeToast, clearToasts };
};

export const useModal = () => {
  const { modals, openModal, closeModal, closeAllModals } = useUiStore();
  
  const confirm = (
    title: string,
    content: string,
    onConfirm?: () => void,
    onCancel?: () => void
  ) => {
    openModal({
      type: 'confirm',
      title,
      content,
      onConfirm,
      onCancel,
      confirmText: '확인',
      cancelText: '취소'
    });
  };
  
  const alert = (title: string, content: string, onConfirm?: () => void) => {
    openModal({
      type: 'alert',
      title,
      content,
      onConfirm,
      confirmText: '확인'
    });
  };
  
  return { modals, openModal, closeModal, closeAllModals, confirm, alert };
};
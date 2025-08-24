import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatPanel from '../../components/ChatPanel';

describe('ChatPanel Component', () => {
  const mockOnSendMessage = vi.fn();
  const mockOnSubmitWord = vi.fn();
  
  const defaultProps = {
    messages: [],
    isConnected: true,
    currentUserId: 1,
    onSendMessage: mockOnSendMessage,
    isMyTurn: false,
    currentChar: '',
    onSubmitWord: mockOnSubmitWord
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat panel with correct title', () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getByText('💬 채팅')).toBeInTheDocument();
  });

  it('shows word input title when its my turn', () => {
    render(<ChatPanel {...defaultProps} isMyTurn={true} />);
    expect(screen.getByText('🎯 단어 입력')).toBeInTheDocument();
  });

  it('displays connection status indicator', () => {
    const { container } = render(<ChatPanel {...defaultProps} />);
    expect(container.querySelector('.bg-green-400')).toBeInTheDocument();
    
    const { container: disconnected } = render(<ChatPanel {...defaultProps} isConnected={false} />);
    expect(disconnected.querySelector('.bg-red-400')).toBeInTheDocument();
  });

  it('shows empty state when no messages', () => {
    render(<ChatPanel {...defaultProps} />);
    expect(screen.getByText('아직 채팅 메시지가 없습니다')).toBeInTheDocument();
  });

  it('renders messages correctly', () => {
    const messages = [
      {
        id: '1',
        userId: 1,
        nickname: '사용자1',
        message: '안녕하세요',
        timestamp: new Date().toISOString(),
        type: 'user' as const
      },
      {
        id: '2',
        userId: 2,
        nickname: '사용자2',
        message: '반갑습니다',
        timestamp: new Date().toISOString(),
        type: 'user' as const
      }
    ];
    
    render(<ChatPanel {...defaultProps} messages={messages} />);
    expect(screen.getByText('안녕하세요')).toBeInTheDocument();
    expect(screen.getByText('반갑습니다')).toBeInTheDocument();
    expect(screen.getByText('나')).toBeInTheDocument(); // 현재 사용자
    expect(screen.getByText('사용자2')).toBeInTheDocument();
  });

  it('renders system messages with correct style', () => {
    const messages = [
      {
        id: '1',
        userId: 0,
        nickname: '시스템',
        message: '게임이 시작되었습니다',
        timestamp: new Date().toISOString(),
        type: 'system' as const
      }
    ];
    
    const { container } = render(<ChatPanel {...defaultProps} messages={messages} />);
    expect(screen.getByText('게임이 시작되었습니다')).toBeInTheDocument();
    expect(container.querySelector('[class*="from-red-"]')).toBeInTheDocument();
  });

  it('sends message on button click', () => {
    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText('메시지를 입력하세요...');
    const button = screen.getByText('전송');
    
    fireEvent.change(input, { target: { value: '테스트 메시지' } });
    fireEvent.click(button);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('테스트 메시지');
    expect(input).toHaveValue('');
  });

  it('submits word when its my turn', () => {
    render(<ChatPanel {...defaultProps} isMyTurn={true} />);
    const input = screen.getByPlaceholderText('단어를 입력하세요...');
    const button = screen.getByText('🚀 제출');
    
    fireEvent.change(input, { target: { value: '사과' } });
    fireEvent.click(button);
    
    expect(mockOnSubmitWord).toHaveBeenCalledWith('사과');
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('shows current character hint when its my turn', () => {
    render(<ChatPanel {...defaultProps} isMyTurn={true} currentChar="가" />);
    expect(screen.getByText(/로 시작하는 단어를 입력하세요!/)).toBeInTheDocument();
  });

  it('disables input when disconnected', () => {
    render(<ChatPanel {...defaultProps} isConnected={false} />);
    const input = screen.getByPlaceholderText('연결 끊김');
    expect(input).toBeDisabled();
  });

  it('shows disconnection message', () => {
    render(<ChatPanel {...defaultProps} isConnected={false} />);
    expect(screen.getByText('연결이 끊어졌습니다. 재연결을 기다리는 중...')).toBeInTheDocument();
  });

  it('handles Enter key press', () => {
    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText('메시지를 입력하세요...');
    
    fireEvent.change(input, { target: { value: '엔터 테스트' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('엔터 테스트');
  });

  it('does not send empty messages', () => {
    render(<ChatPanel {...defaultProps} />);
    const button = screen.getByText('전송');
    
    fireEvent.click(button);
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('shows character count', () => {
    render(<ChatPanel {...defaultProps} />);
    const input = screen.getByPlaceholderText('메시지를 입력하세요...');
    
    fireEvent.change(input, { target: { value: '테스트' } });
    expect(screen.getByText('3/200')).toBeInTheDocument();
  });

  it('applies correct placeholder based on turn and connection', () => {
    const { rerender } = render(<ChatPanel {...defaultProps} />);
    expect(screen.getByPlaceholderText('메시지를 입력하세요...')).toBeInTheDocument();
    
    rerender(<ChatPanel {...defaultProps} isMyTurn={true} currentChar="나" />);
    expect(screen.getByPlaceholderText('나로 시작하는 단어...')).toBeInTheDocument();
    
    rerender(<ChatPanel {...defaultProps} isConnected={false} />);
    expect(screen.getByPlaceholderText('연결 끊김')).toBeInTheDocument();
  });
});
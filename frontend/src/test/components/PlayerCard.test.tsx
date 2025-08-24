import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PlayerCard from '../../components/ui/PlayerCard';

describe('PlayerCard Component', () => {
  const defaultProps = {
    id: '1',
    nickname: '플레이어1'
  };

  it('renders player nickname correctly', () => {
    render(<PlayerCard {...defaultProps} />);
    expect(screen.getByText('플레이어1')).toBeInTheDocument();
  });

  it('shows "나" suffix when isMe is true', () => {
    render(<PlayerCard {...defaultProps} isMe={true} />);
    expect(screen.getByText('플레이어1 (나)')).toBeInTheDocument();
  });

  it('displays host badge when isHost is true', () => {
    render(<PlayerCard {...defaultProps} isHost={true} />);
    expect(screen.getByText('방장')).toBeInTheDocument();
  });

  it('displays turn badge when isCurrentTurn is true', () => {
    render(<PlayerCard {...defaultProps} isCurrentTurn={true} />);
    expect(screen.getByText('턴')).toBeInTheDocument();
  });

  it('shows score when provided', () => {
    render(<PlayerCard {...defaultProps} score={150} />);
    expect(screen.getByText('🏆 150점')).toBeInTheDocument();
  });

  it('displays ready status correctly', () => {
    const { rerender } = render(<PlayerCard {...defaultProps} isReady={true} />);
    expect(screen.getByText('준비완료')).toBeInTheDocument();
    
    rerender(<PlayerCard {...defaultProps} isReady={false} />);
    expect(screen.getByText('대기중')).toBeInTheDocument();
  });

  it('shows disconnected status when not connected', () => {
    render(<PlayerCard {...defaultProps} isConnected={false} />);
    expect(screen.getByText('연결끊김')).toBeInTheDocument();
  });

  it('applies correct styles for current turn', () => {
    const { container } = render(<PlayerCard {...defaultProps} isCurrentTurn={true} />);
    expect(container.querySelector('[class*="from-green-"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="animate-pulse-slow"]')).toBeInTheDocument();
  });

  it('applies correct styles for ready state', () => {
    const { container } = render(<PlayerCard {...defaultProps} isReady={true} />);
    expect(container.querySelector('[class*="from-blue-"]')).toBeInTheDocument();
  });

  it('applies correct styles for current player', () => {
    const { container } = render(<PlayerCard {...defaultProps} isMe={true} />);
    expect(container.querySelector('[class*="from-purple-"]')).toBeInTheDocument();
  });

  it('shows correct status icon', () => {
    const { container: disconnected } = render(<PlayerCard {...defaultProps} isConnected={false} />);
    expect(disconnected.textContent).toContain('🔌');
    
    const { container: currentTurn } = render(<PlayerCard {...defaultProps} isCurrentTurn={true} />);
    expect(currentTurn.textContent).toContain('🎯');
    
    const { container: ready } = render(<PlayerCard {...defaultProps} isReady={true} />);
    expect(ready.textContent).toContain('✅');
    
    const { container: host } = render(<PlayerCard {...defaultProps} isHost={true} />);
    expect(host.textContent).toContain('👑');
  });

  it('applies bounce animation for current turn', () => {
    const { container } = render(<PlayerCard {...defaultProps} isCurrentTurn={true} />);
    expect(container.querySelector('.animate-bounce')).toBeInTheDocument();
  });

  it('shows multiple badges simultaneously', () => {
    render(<PlayerCard {...defaultProps} isHost={true} isCurrentTurn={true} />);
    expect(screen.getByText('방장')).toBeInTheDocument();
    expect(screen.getByText('턴')).toBeInTheDocument();
  });
});
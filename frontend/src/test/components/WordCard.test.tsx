import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import WordCard from '../../components/ui/WordCard';

describe('WordCard Component', () => {
  const defaultProps = {
    word: '사과',
    index: 0
  };

  it('renders word correctly', () => {
    render(<WordCard {...defaultProps} />);
    expect(screen.getByText('사과')).toBeInTheDocument();
  });

  it('displays score when provided', () => {
    render(<WordCard {...defaultProps} score={20} />);
    expect(screen.getByText('20점')).toBeInTheDocument();
  });

  it('displays definition when provided', () => {
    const definition = '먹는 과일';
    render(<WordCard {...defaultProps} definition={definition} />);
    expect(screen.getByText(definition)).toBeInTheDocument();
  });

  it('shows correct difficulty text', () => {
    render(<WordCard {...defaultProps} difficulty={1} />);
    expect(screen.getByText('쉬움')).toBeInTheDocument();
    
    render(<WordCard {...defaultProps} difficulty={2} />);
    expect(screen.getByText('보통')).toBeInTheDocument();
    
    render(<WordCard {...defaultProps} difficulty={3} />);
    expect(screen.getByText('어려움')).toBeInTheDocument();
  });

  it('applies correct difficulty colors', () => {
    const { container: container1 } = render(<WordCard {...defaultProps} difficulty={1} />);
    expect(container1.querySelector('.from-green-400')).toBeInTheDocument();
    
    const { container: container2 } = render(<WordCard {...defaultProps} difficulty={2} />);
    expect(container2.querySelector('.from-yellow-400')).toBeInTheDocument();
    
    const { container: container3 } = render(<WordCard {...defaultProps} difficulty={3} />);
    expect(container3.querySelector('.from-red-400')).toBeInTheDocument();
  });

  it('displays character count', () => {
    render(<WordCard {...defaultProps} word="안녕하세요" />);
    expect(screen.getByText('5글자')).toBeInTheDocument();
  });

  it('applies latest card styles when isLatest is true', () => {
    const { container } = render(<WordCard {...defaultProps} isLatest={true} />);
    expect(container.querySelector('.animate-bounce-in')).toBeInTheDocument();
    expect(container.querySelector('.ring-2')).toBeInTheDocument();
  });

  it('applies animation delay based on index', () => {
    const { container } = render(<WordCard {...defaultProps} index={2} />);
    const card = container.firstChild as HTMLElement;
    expect(card.style.animationDelay).toBe('200ms');
  });

  it('does not show definition if it matches default pattern', () => {
    render(<WordCard {...defaultProps} definition="사과의 뜻" />);
    const definitionElement = screen.queryByText('사과의 뜻');
    expect(definitionElement).not.toBeInTheDocument();
  });
});
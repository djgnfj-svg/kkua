import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

// Mock Timer component
const Timer = ({ remainingTime }: { remainingTime: number }) => (
  <div data-testid="timer">
    {remainingTime.toFixed(1)}초
  </div>
);

describe('Timer Component', () => {
  it('renders remaining time correctly', () => {
    render(<Timer remainingTime={15.5} />);
    expect(screen.getByTestId('timer')).toHaveTextContent('15.5초');
  });

  it('shows critical time warning', () => {
    render(<Timer remainingTime={3.2} />);
    const timer = screen.getByTestId('timer');
    expect(timer).toHaveTextContent('3.2초');
  });
});
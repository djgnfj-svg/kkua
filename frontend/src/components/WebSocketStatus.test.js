import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import WebSocketStatus from './WebSocketStatus';

describe('WebSocketStatus Component', () => {
  test('shows connected status', () => {
    render(
      <WebSocketStatus 
        connected={true}
        isReconnecting={false}
        connectionAttempts={0}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.getByText('실시간 연결됨')).toBeInTheDocument();
    expect(screen.getByTestId('connection-indicator')).toHaveClass('bg-green-500');
  });

  test('shows disconnected status', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={false}
        connectionAttempts={0}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.getByText('연결 끊김')).toBeInTheDocument();
    expect(screen.getByTestId('connection-indicator')).toHaveClass('bg-red-500');
  });

  test('shows reconnecting status', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={true}
        connectionAttempts={2}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.getByText('재연결 중... (2/5)')).toBeInTheDocument();
    expect(screen.getByTestId('connection-indicator')).toHaveClass('bg-yellow-500');
  });

  test('shows manual reconnect button when max attempts reached', () => {
    const mockReconnect = jest.fn();
    
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={false}
        connectionAttempts={5}
        maxReconnectAttempts={5}
        onManualReconnect={mockReconnect}
      />
    );

    const reconnectButton = screen.getByText('수동 재연결');
    expect(reconnectButton).toBeInTheDocument();

    fireEvent.click(reconnectButton);
    expect(mockReconnect).toHaveBeenCalled();
  });

  test('does not show manual reconnect button when connected', () => {
    render(
      <WebSocketStatus 
        connected={true}
        isReconnecting={false}
        connectionAttempts={5}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.queryByText('수동 재연결')).not.toBeInTheDocument();
  });

  test('does not show manual reconnect button when reconnecting', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={true}
        connectionAttempts={3}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.queryByText('수동 재연결')).not.toBeInTheDocument();
  });

  test('shows progress indicator when reconnecting', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={true}
        connectionAttempts={2}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    const progressBar = screen.getByTestId('reconnection-progress');
    expect(progressBar).toBeInTheDocument();
    
    // Check if progress is calculated correctly (2/5 * 100 = 40%)
    expect(progressBar).toHaveStyle({ width: '40%' });
  });

  test('handles zero max attempts gracefully', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={false}
        connectionAttempts={0}
        maxReconnectAttempts={0}
        onManualReconnect={() => {}}
      />
    );

    expect(screen.getByText('연결 끊김')).toBeInTheDocument();
  });

  test('handles edge case when attempts exceed max attempts', () => {
    render(
      <WebSocketStatus 
        connected={false}
        isReconnecting={false}
        connectionAttempts={7}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    // Should still show manual reconnect button
    expect(screen.getByText('수동 재연결')).toBeInTheDocument();
  });

  test('applies correct CSS classes for connection states', () => {
    const { rerender } = render(
      <WebSocketStatus 
        connected={true}
        isReconnecting={false}
        connectionAttempts={0}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    let indicator = screen.getByTestId('connection-indicator');
    expect(indicator).toHaveClass('bg-green-500');

    rerender(
      <WebSocketStatus 
        connected={false}
        isReconnecting={true}
        connectionAttempts={1}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    indicator = screen.getByTestId('connection-indicator');
    expect(indicator).toHaveClass('bg-yellow-500');

    rerender(
      <WebSocketStatus 
        connected={false}
        isReconnecting={false}
        connectionAttempts={5}
        maxReconnectAttempts={5}
        onManualReconnect={() => {}}
      />
    );

    indicator = screen.getByTestId('connection-indicator');
    expect(indicator).toHaveClass('bg-red-500');
  });
});
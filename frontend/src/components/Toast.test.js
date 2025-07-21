import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Toast from './Toast';

describe('Toast Component', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('renders toast message', () => {
    render(
      <Toast
        message="Test message"
        type="info"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  test('applies correct styling for success type', () => {
    render(
      <Toast
        message="Success message"
        type="success"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const toast = screen.getByText('Success message').parentElement;
    expect(toast).toHaveClass('bg-green-500');
  });

  test('applies correct styling for error type', () => {
    render(
      <Toast
        message="Error message"
        type="error"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const toast = screen.getByText('Error message').parentElement;
    expect(toast).toHaveClass('bg-red-500');
  });

  test('applies correct styling for warning type', () => {
    render(
      <Toast
        message="Warning message"
        type="warning"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const toast = screen.getByText('Warning message').parentElement;
    expect(toast).toHaveClass('bg-yellow-500');
  });

  test('applies default info styling', () => {
    render(
      <Toast
        message="Info message"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const toast = screen.getByText('Info message').parentElement;
    expect(toast).toHaveClass('bg-blue-500');
  });

  test('calls onClose after duration', async () => {
    render(
      <Toast
        message="Test message"
        type="info"
        onClose={mockOnClose}
        duration={1000}
      />
    );

    // Fast-forward time
    jest.advanceTimersByTime(1000);
    
    // Wait for fade out animation
    jest.advanceTimersByTime(300);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  test('handles missing onClose prop gracefully', () => {
    expect(() => {
      render(
        <Toast
          message="Test message"
          type="info"
          duration={1000}
        />
      );
    }).not.toThrow();
  });

  test('starts with visible state', () => {
    render(
      <Toast
        message="Test message"
        type="info"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const toast = screen.getByText('Test message').parentElement;
    expect(toast).toHaveClass('opacity-100');
  });

  test('handles close button click', async () => {
    render(
      <Toast
        message="Test message"
        type="info"
        onClose={mockOnClose}
        duration={3000}
      />
    );

    const closeButton = screen.getByText('×');
    closeButton.click();

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});
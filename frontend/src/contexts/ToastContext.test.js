import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastProvider, useToast } from './ToastContext';

// Test component to use the toast context
const TestComponent = () => {
  const { showSuccess, showError, showWarning, showInfo } = useToast();

  return (
    <div>
      <button onClick={() => showSuccess('Success message', 1000)}>
        Show Success
      </button>
      <button onClick={() => showError('Error message', 1000)}>
        Show Error
      </button>
      <button onClick={() => showWarning('Warning message', 1000)}>
        Show Warning
      </button>
      <button onClick={() => showInfo('Info message', 1000)}>Show Info</button>
    </div>
  );
};

describe('ToastContext', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('throws error when useToast is used outside provider', () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useToast must be used within a ToastProvider');

    console.error = originalError;
  });

  test('shows success toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByText('Show Success');
    act(() => {
      successButton.click();
    });

    expect(screen.getByText('Success message')).toBeInTheDocument();
  });

  test('shows error toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const errorButton = screen.getByText('Show Error');
    act(() => {
      errorButton.click();
    });

    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  test('shows warning toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const warningButton = screen.getByText('Show Warning');
    act(() => {
      warningButton.click();
    });

    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  test('shows info toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const infoButton = screen.getByText('Show Info');
    act(() => {
      infoButton.click();
    });

    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  test('removes toast after duration', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByText('Show Success');
    act(() => {
      successButton.click();
    });

    expect(screen.getByText('Success message')).toBeInTheDocument();

    // Fast-forward time beyond duration + animation time
    act(() => {
      jest.advanceTimersByTime(1300);
    });

    expect(screen.queryByText('Success message')).not.toBeInTheDocument();
  });

  test('handles multiple toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    act(() => {
      screen.getByText('Show Success').click();
      screen.getByText('Show Error').click();
    });

    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  test('generates unique IDs for toasts', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    act(() => {
      screen.getByText('Show Success').click();
      screen.getByText('Show Success').click();
    });

    const toasts = screen.getAllByText('Success message');
    expect(toasts).toHaveLength(2);
  });

  test('uses default duration when not specified', () => {
    const TestComponentDefault = () => {
      const { showInfo } = useToast();
      return (
        <button onClick={() => showInfo('Default duration')}>
          Show Default
        </button>
      );
    };

    render(
      <ToastProvider>
        <TestComponentDefault />
      </ToastProvider>
    );

    act(() => {
      screen.getByText('Show Default').click();
    });

    expect(screen.getByText('Default duration')).toBeInTheDocument();

    // Should still be visible after 1 second (default is 3 seconds)
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(screen.getByText('Default duration')).toBeInTheDocument();

    // Should be removed after default duration + animation time
    act(() => {
      jest.advanceTimersByTime(2300);
    });

    expect(screen.queryByText('Default duration')).not.toBeInTheDocument();
  });
});

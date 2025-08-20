import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Button, Card } from './index';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <Card.Body className="text-center">
              <div className="text-6xl mb-4">😵</div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                앗, 오류가 발생했습니다!
              </h2>
              <p className="text-gray-600 mb-6">
                예상치 못한 문제가 발생했습니다. 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.
              </p>
              <div className="space-y-3">
                <Button 
                  onClick={this.handleRetry}
                  variant="primary"
                  className="w-full"
                >
                  다시 시도
                </Button>
                <Button 
                  onClick={() => window.location.reload()}
                  variant="secondary"
                  className="w-full"
                >
                  페이지 새로고침
                </Button>
              </div>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                    개발자 정보 (개발 환경에서만 표시)
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-red-600 whitespace-pre-wrap overflow-auto">
                    {this.state.error.toString()}
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </Card.Body>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
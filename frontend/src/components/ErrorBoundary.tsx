import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Card } from './ui';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return { 
      hasError: true, 
      error, 
      errorInfo: null 
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // 에러 로깅 (실제 환경에서는 Sentry 등 사용)
    if (process.env.NODE_ENV === 'production') {
      this.logErrorToService(error, errorInfo);
    }
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // 실제 에러 로깅 서비스로 전송
    console.error('Error logged to service:', {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <Card.Body>
              <div className="text-center space-y-4">
                <div className="text-6xl mb-4">😵</div>
                <h2 className="text-xl font-bold text-gray-900">
                  앗, 오류가 발생했습니다!
                </h2>
                <p className="text-gray-600">
                  예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 다시 시도해주세요.
                </p>
                
                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details className="text-left bg-gray-100 p-3 rounded text-sm">
                    <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                      개발자 정보
                    </summary>
                    <div className="space-y-2 text-gray-600">
                      <div>
                        <strong>오류:</strong> {this.state.error.message}
                      </div>
                      {this.state.errorInfo && (
                        <div>
                          <strong>컴포넌트 스택:</strong>
                          <pre className="whitespace-pre-wrap text-xs mt-1">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </details>
                )}

                <div className="flex flex-col sm:flex-row gap-3">
                  <Button
                    onClick={this.handleReset}
                    variant="secondary"
                    className="flex-1"
                  >
                    다시 시도
                  </Button>
                  <Button
                    onClick={this.handleReload}
                    variant="primary"
                    className="flex-1"
                  >
                    페이지 새로고침
                  </Button>
                </div>

                <Button
                  onClick={() => window.location.href = '/lobby'}
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2"
                >
                  로비로 돌아가기
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
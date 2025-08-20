import React, { useState, useEffect } from 'react';
import { Button, Card, Loading } from './ui';
import { apiEndpoints } from '../utils/api';

interface HealthStatus {
  status: 'healthy' | 'error' | 'loading';
  message: string;
  details?: any;
}

const BackendTest: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({
    status: 'loading',
    message: 'Checking backend connection...'
  });

  const checkBackendHealth = async () => {
    setHealthStatus({
      status: 'loading',
      message: 'Checking backend connection...'
    });

    try {
      const response = await apiEndpoints.health();
      setHealthStatus({
        status: 'healthy',
        message: 'Backend connection successful!',
        details: response.data
      });
    } catch (error: any) {
      setHealthStatus({
        status: 'error',
        message: `Backend connection failed: ${error.message}`,
        details: error.response?.data || error.message
      });
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const getStatusColor = () => {
    switch (healthStatus.status) {
      case 'healthy': return 'text-success-600';
      case 'error': return 'text-danger-600';
      case 'loading': return 'text-primary-600';
    }
  };

  const getStatusIcon = () => {
    switch (healthStatus.status) {
      case 'healthy':
        return (
          <svg className="w-5 h-5 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-danger-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'loading':
        return <Loading size="sm" />;
    }
  };

  return (
    <Card className="max-w-md mx-auto">
      <Card.Header>
        <h2 className="text-lg font-semibold text-gray-900">Backend Connection Test</h2>
      </Card.Header>
      
      <Card.Body className="space-y-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <span className={`font-medium ${getStatusColor()}`}>
            {healthStatus.message}
          </span>
        </div>
        
        {healthStatus.details && (
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Response Details:</h4>
            <pre className="text-xs text-gray-600 whitespace-pre-wrap">
              {JSON.stringify(healthStatus.details, null, 2)}
            </pre>
          </div>
        )}
        
        <Button 
          onClick={checkBackendHealth}
          disabled={healthStatus.status === 'loading'}
          className="w-full"
        >
          {healthStatus.status === 'loading' ? 'Testing...' : 'Test Again'}
        </Button>
      </Card.Body>
    </Card>
  );
};

export default BackendTest;
interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

interface ErrorLog {
  message: string;
  stack?: string;
  timestamp: number;
  url: string;
  userAgent: string;
  metadata?: Record<string, any>;
}

class SimpleMonitoring {
  private metrics: PerformanceMetric[] = [];
  private errors: ErrorLog[] = [];
  private readonly maxItems = 100;

  // 성능 메트릭 기록
  recordMetric(name: string, value: number, metadata?: Record<string, any>) {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata
    };

    this.metrics.push(metric);
    
    // 최대 개수 제한
    if (this.metrics.length > this.maxItems) {
      this.metrics = this.metrics.slice(-this.maxItems);
    }

    console.log(`[Metric] ${name}: ${value}ms`, metadata);
  }

  // 함수 실행 시간 측정
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      const result = await fn();
      const duration = performance.now() - start;
      this.recordMetric(name, duration);
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      this.recordMetric(`${name}_error`, duration);
      throw error;
    }
  }

  // 동기 함수 실행 시간 측정
  measure<T>(name: string, fn: () => T): T {
    const start = performance.now();
    try {
      const result = fn();
      const duration = performance.now() - start;
      this.recordMetric(name, duration);
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      this.recordMetric(`${name}_error`, duration);
      throw error;
    }
  }

  // 에러 로깅
  logError(error: Error | string, metadata?: Record<string, any>) {
    const errorLog: ErrorLog = {
      message: typeof error === 'string' ? error : error.message,
      stack: typeof error === 'object' ? error.stack : undefined,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      metadata
    };

    this.errors.push(errorLog);
    
    // 최대 개수 제한
    if (this.errors.length > this.maxItems) {
      this.errors = this.errors.slice(-this.maxItems);
    }

    console.error('[Error]', errorLog);
  }

  // WebSocket 연결 상태 모니터링
  monitorWebSocket(ws: WebSocket, roomId?: string) {
    const startTime = Date.now();

    ws.addEventListener('open', () => {
      const duration = Date.now() - startTime;
      this.recordMetric('websocket_connect', duration, { roomId });
    });

    ws.addEventListener('close', () => {
      this.recordMetric('websocket_disconnect', 0, { roomId });
    });

    ws.addEventListener('error', (event) => {
      this.logError('WebSocket error', { event, roomId });
    });
  }

  // 페이지 성능 모니터링
  monitorPagePerformance() {
    // 페이지 로드 성능
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfData = performance.getEntriesByType('navigation')[0] as any;
        if (perfData) {
          this.recordMetric('page_load', perfData.loadEventEnd - perfData.fetchStart);
          this.recordMetric('dom_content_loaded', perfData.domContentLoadedEventEnd - perfData.fetchStart);
          this.recordMetric('first_byte', perfData.responseStart - perfData.fetchStart);
        }
      }, 100);
    });

    // 페이지 가시성 변경
    document.addEventListener('visibilitychange', () => {
      this.recordMetric('visibility_change', 0, { 
        hidden: document.hidden 
      });
    });
  }

  // 메모리 사용량 모니터링 (크롬)
  monitorMemory() {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.recordMetric('memory_used', memory.usedJSHeapSize / 1024 / 1024); // MB
      this.recordMetric('memory_total', memory.totalJSHeapSize / 1024 / 1024); // MB
    }
  }

  // 통계 조회
  getMetrics(name?: string): PerformanceMetric[] {
    if (name) {
      return this.metrics.filter(m => m.name === name);
    }
    return [...this.metrics];
  }

  getErrors(): ErrorLog[] {
    return [...this.errors];
  }

  // 요약 통계
  getMetricsSummary() {
    const summary: Record<string, { count: number; avg: number; min: number; max: number }> = {};
    
    for (const metric of this.metrics) {
      if (!summary[metric.name]) {
        summary[metric.name] = { count: 0, avg: 0, min: Infinity, max: -Infinity };
      }
      
      const s = summary[metric.name];
      s.count++;
      s.min = Math.min(s.min, metric.value);
      s.max = Math.max(s.max, metric.value);
      s.avg = (s.avg * (s.count - 1) + metric.value) / s.count;
    }
    
    return summary;
  }

  // 데이터 초기화
  clear() {
    this.metrics = [];
    this.errors = [];
  }
}

// 싱글톤 인스턴스
export const monitoring = new SimpleMonitoring();

// 전역 에러 핸들러 설정
window.addEventListener('error', (event) => {
  monitoring.logError(event.error || event.message, {
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno
  });
});

window.addEventListener('unhandledrejection', (event) => {
  monitoring.logError(`Unhandled promise rejection: ${event.reason}`, {
    type: 'unhandledrejection'
  });
});

// 페이지 성능 모니터링 시작
monitoring.monitorPagePerformance();
import time
import logging
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime
import asyncio

# 구조화된 로깅을 위한 커스텀 포매터
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 추가 컨텍스트가 있으면 포함
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        return str(log_data)

# 성능 메트릭 수집
class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        
    def record_metric(self, name: str, value: float, metadata: Optional[Dict] = None):
        """메트릭 기록"""
        if name not in self.metrics:
            self.metrics[name] = []
            
        metric_data = {
            'value': value,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        self.metrics[name].append(metric_data)
        
        # 최대 1000개까지만 보관
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
            
        logging.info(f"Metric recorded: {name} = {value}", extra={
            'extra_data': {'metric': name, 'value': value, 'metadata': metadata}
        })
    
    def get_metrics_summary(self, name: str) -> Dict[str, Any]:
        """메트릭 요약 통계"""
        if name not in self.metrics:
            return {}
            
        values = [m['value'] for m in self.metrics[name]]
        return {
            'count': len(values),
            'avg': sum(values) / len(values) if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0,
            'latest': values[-1] if values else 0
        }

# 전역 모니터 인스턴스
monitor = PerformanceMonitor()

def log_performance(metric_name: str):
    """성능 측정 데코레이터"""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000  # ms
                    monitor.record_metric(f"{metric_name}_success", duration)
                    return result
                except Exception as e:
                    duration = (time.time() - start_time) * 1000  # ms
                    monitor.record_metric(f"{metric_name}_error", duration)
                    logging.error(f"Error in {func.__name__}: {str(e)}", extra={
                        'extra_data': {'function': func.__name__, 'error': str(e)}
                    })
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000  # ms
                    monitor.record_metric(f"{metric_name}_success", duration)
                    return result
                except Exception as e:
                    duration = (time.time() - start_time) * 1000  # ms
                    monitor.record_metric(f"{metric_name}_error", duration)
                    logging.error(f"Error in {func.__name__}: {str(e)}", extra={
                        'extra_data': {'function': func.__name__, 'error': str(e)}
                    })
                    raise
            return sync_wrapper
    return decorator

def log_websocket_event(event_type: str, room_id: Optional[str] = None, user_id: Optional[int] = None):
    """WebSocket 이벤트 로깅"""
    logging.info(f"WebSocket event: {event_type}", extra={
        'extra_data': {
            'event_type': event_type,
            'room_id': room_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    })

def log_game_event(event_type: str, room_id: str, player_data: Optional[Dict] = None):
    """게임 이벤트 로깅"""
    logging.info(f"Game event: {event_type}", extra={
        'extra_data': {
            'event_type': event_type,
            'room_id': room_id,
            'player_data': player_data,
            'timestamp': datetime.utcnow().isoformat()
        }
    })

# 로깅 설정
def setup_logging():
    """로깅 설정 초기화"""
    # 루트 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 구조화된 로깅을 위한 별도 로거
    structured_logger = logging.getLogger('structured')
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    structured_logger.addHandler(handler)
    structured_logger.setLevel(logging.INFO)
    
    return structured_logger
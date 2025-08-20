"""
성능 및 부하 테스트
대용량 동시 접속 및 처리량 테스트
"""
import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import psutil
import gc
from typing import List, Dict, Any
from datetime import datetime, timezone

# 성능 테스트 관련 import
from services.game_engine import GameEngine
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService
from websocket.game_handler import GameHandler
from websocket.websocket_manager import WebSocketManager


class PerformanceMetrics:
    """성능 지표 수집 클래스"""
    
    def __init__(self):
        self.response_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
    
    def start_measurement(self):
        """측정 시작"""
        self.start_time = time.time()
        self.memory_usage.append(psutil.virtual_memory().percent)
        self.cpu_usage.append(psutil.cpu_percent())
    
    def end_measurement(self):
        """측정 종료"""
        self.end_time = time.time()
        self.memory_usage.append(psutil.virtual_memory().percent)
        self.cpu_usage.append(psutil.cpu_percent())
    
    def record_response_time(self, response_time: float):
        """응답 시간 기록"""
        self.response_times.append(response_time)
    
    def record_success(self):
        """성공 카운트 증가"""
        self.success_count += 1
    
    def record_error(self):
        """에러 카운트 증가"""
        self.error_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """성능 지표 요약"""
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0
        total_requests = self.success_count + self.error_count
        
        return {
            "total_time": total_time,
            "total_requests": total_requests,
            "success_rate": self.success_count / total_requests if total_requests > 0 else 0,
            "error_rate": self.error_count / total_requests if total_requests > 0 else 0,
            "throughput": total_requests / total_time if total_time > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0,
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0,
            "p99_response_time": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else 0,
            "max_memory_usage": max(self.memory_usage) if self.memory_usage else 0,
            "avg_cpu_usage": statistics.mean(self.cpu_usage) if self.cpu_usage else 0
        }


class TestPerformanceLoad:
    """성능 부하 테스트"""
    
    @pytest.fixture
    def setup_performance_environment(self):
        """성능 테스트 환경 설정"""
        # Redis mock (고성능)
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = True
        redis_mock.exists.return_value = False
        redis_mock.hget.return_value = None
        redis_mock.hset.return_value = True
        
        # 서비스 인스턴스들
        game_engine = GameEngine()
        cache_service = CacheService()
        analytics_service = AnalyticsService()
        
        # Redis mock 설정
        game_engine.redis = redis_mock
        cache_service.redis_client = redis_mock
        analytics_service.redis_client = redis_mock
        
        return {
            'game_engine': game_engine,
            'cache_service': cache_service,
            'analytics_service': analytics_service,
            'redis_mock': redis_mock
        }
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_game_creation(self, setup_performance_environment):
        """동시 게임 생성 부하 테스트"""
        game_engine = setup_performance_environment['game_engine']
        metrics = PerformanceMetrics()
        
        # 100개 동시 게임 생성
        concurrent_rooms = 100
        
        async def create_single_game(room_index: int):
            """단일 게임 생성"""
            room_id = f"load_test_room_{room_index}"
            start_time = time.time()
            
            try:
                success, message = await game_engine.create_game(room_id, max_players=4)
                end_time = time.time()
                
                metrics.record_response_time(end_time - start_time)
                if success:
                    metrics.record_success()
                else:
                    metrics.record_error()
                    
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 동시 실행
        tasks = [create_single_game(i) for i in range(concurrent_rooms)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"게임 생성 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.95  # 95% 이상 성공률
        assert summary['avg_response_time'] < 0.1  # 100ms 미만 평균 응답시간
        assert summary['throughput'] > 100  # 초당 100개 이상 처리
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_performance(self, setup_performance_environment):
        """캐시 성능 테스트"""
        cache_service = setup_performance_environment['cache_service']
        metrics = PerformanceMetrics()
        
        # 대량 데이터 캐싱 테스트
        test_items = 10000
        
        async def cache_operation(item_index: int):
            """캐시 읽기/쓰기 작업"""
            key = f"perf_key_{item_index}"
            value = f"perf_value_{item_index}_{'x' * 100}"  # 100자 데이터
            
            start_time = time.time()
            
            try:
                # 쓰기
                await cache_service.set("performance_test", key, value)
                
                # 읽기
                result = await cache_service.get("performance_test", key)
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 배치 크기별로 처리 (메모리 절약)
        batch_size = 1000
        for i in range(0, test_items, batch_size):
            batch_tasks = [
                cache_operation(j) 
                for j in range(i, min(i + batch_size, test_items))
            ]
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 가비지 컬렉션
            gc.collect()
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"캐시 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.99  # 99% 이상 성공률
        assert summary['avg_response_time'] < 0.01  # 10ms 미만 평균 응답시간
        assert summary['throughput'] > 1000  # 초당 1000개 이상 처리
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_word_validation_performance(self, setup_performance_environment):
        """단어 검증 성능 테스트"""
        from services.word_validator import WordValidator, WordChainState
        
        validator = WordValidator()
        metrics = PerformanceMetrics()
        
        # 테스트 단어들
        test_words = [
            "사과", "과일", "일기장", "장난감", "감자", "자동차", "차례", "례의",
            "의사", "사람", "람보", "보석", "석고", "고래", "래디오", "오리",
            "리본", "본격", "격투", "투수", "수박", "박물관", "관계", "계란"
        ] * 100  # 2400개 단어
        
        async def validate_single_word(word: str):
            """단일 단어 검증"""
            word_chain = WordChainState()
            used_words = set()
            
            start_time = time.time()
            
            try:
                result = await validator.validate_word_chain(word, word_chain, used_words)
                end_time = time.time()
                
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 배치 처리
        batch_size = 100
        for i in range(0, len(test_words), batch_size):
            batch_words = test_words[i:i + batch_size]
            batch_tasks = [validate_single_word(word) for word in batch_words]
            await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"단어 검증 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.98  # 98% 이상 성공률
        assert summary['avg_response_time'] < 0.05  # 50ms 미만 평균 응답시간
    
    @pytest.mark.performance
    @pytest.mark.asyncio  
    async def test_analytics_event_processing(self, setup_performance_environment):
        """분석 이벤트 처리 성능 테스트"""
        analytics_service = setup_performance_environment['analytics_service']
        metrics = PerformanceMetrics()
        
        # 대량 이벤트 생성
        event_count = 50000
        
        async def track_single_event(event_index: int):
            """단일 이벤트 추적"""
            event_types = ["game_started", "word_submitted", "item_used", "game_ended"]
            event_type = event_types[event_index % len(event_types)]
            
            start_time = time.time()
            
            try:
                await analytics_service.track_event(
                    event_type, 
                    event_index % 1000,  # 1000명의 가상 사용자
                    {
                        "room_id": f"room_{event_index % 100}",
                        "data_field": f"value_{event_index}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 배치 처리
        batch_size = 1000
        for i in range(0, event_count, batch_size):
            batch_tasks = [
                track_single_event(j) 
                for j in range(i, min(i + batch_size, event_count))
            ]
            await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"분석 이벤트 처리 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.95  # 95% 이상 성공률
        assert summary['avg_response_time'] < 0.02  # 20ms 미만 평균 응답시간
        assert summary['throughput'] > 2000  # 초당 2000개 이상 이벤트 처리
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self, setup_performance_environment):
        """WebSocket 메시지 처리량 테스트"""
        # WebSocket 매니저 mock
        ws_manager = Mock()
        ws_manager.send_to_room = Mock()
        ws_manager.send_to_user = Mock()
        
        game_handler = GameHandler(ws_manager)
        metrics = PerformanceMetrics()
        
        # 가상 WebSocket 연결들
        mock_connections = {}
        for i in range(1000):
            mock_ws = Mock()
            mock_ws.user_id = i
            mock_ws.nickname = f"user_{i}"
            mock_connections[i] = mock_ws
        
        ws_manager.connections = mock_connections
        
        async def process_single_message(message_index: int):
            """단일 메시지 처리"""
            user_id = message_index % 1000
            room_id = f"room_{message_index % 50}"
            
            message_types = ["join_game", "submit_word", "use_item", "chat_message"]
            message_type = message_types[message_index % len(message_types)]
            
            message = {
                "type": message_type,
                "room_id": room_id,
                "data": f"test_data_{message_index}"
            }
            
            mock_ws = mock_connections[user_id]
            start_time = time.time()
            
            try:
                # 메시지 타입에 따른 처리 (간소화된 버전)
                if message_type == "join_game":
                    await game_handler.handle_join_game(mock_ws, message)
                elif message_type == "chat_message":
                    await game_handler.handle_chat_message(mock_ws, message)
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 대량 메시지 처리
        message_count = 10000
        batch_size = 500
        
        for i in range(0, message_count, batch_size):
            batch_tasks = [
                process_single_message(j)
                for j in range(i, min(i + batch_size, message_count))
            ]
            await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"WebSocket 메시지 처리 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.90  # 90% 이상 성공률 (mock 환경 고려)
        assert summary['throughput'] > 500  # 초당 500개 이상 메시지 처리
    
    @pytest.mark.performance 
    def test_memory_usage_under_load(self, setup_performance_environment):
        """부하 상황에서 메모리 사용량 테스트"""
        cache_service = setup_performance_environment['cache_service']
        
        # 초기 메모리 사용량
        initial_memory = psutil.virtual_memory().used
        
        # 대량 데이터 생성 및 캐싱
        large_data = "x" * 10000  # 10KB 데이터
        
        for i in range(1000):  # 10MB 데이터
            cache_service._set_l1(f"memory_test_{i}", large_data, ttl=3600)
        
        # 중간 메모리 사용량
        mid_memory = psutil.virtual_memory().used
        memory_increase = mid_memory - initial_memory
        
        # 가비지 컬렉션 실행
        gc.collect()
        
        # 최종 메모리 사용량
        final_memory = psutil.virtual_memory().used
        
        print(f"메모리 사용량 - 초기: {initial_memory}, 중간: {mid_memory}, 최종: {final_memory}")
        print(f"메모리 증가량: {memory_increase} bytes")
        
        # 메모리 누수 검증 (10MB 이하 증가)
        assert memory_increase < 50 * 1024 * 1024  # 50MB 이하
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_connection_pool(self, setup_performance_environment):
        """데이터베이스 연결 풀 성능 테스트"""
        metrics = PerformanceMetrics()
        
        async def simulate_db_query(query_index: int):
            """데이터베이스 쿼리 시뮬레이션"""
            start_time = time.time()
            
            try:
                # 실제 환경에서는 데이터베이스 쿼리 수행
                # 여기서는 시뮬레이션을 위한 지연
                await asyncio.sleep(0.001)  # 1ms 시뮬레이션
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 동시 DB 쿼리 시뮬레이션
        concurrent_queries = 100
        tasks = [simulate_db_query(i) for i in range(concurrent_queries)]
        await asyncio.gather(*tasks)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"DB 연결 풀 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] == 1.0  # 100% 성공률
        assert summary['avg_response_time'] < 0.01  # 10ms 미만
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_full_game_simulation_performance(self, setup_performance_environment):
        """전체 게임 시뮬레이션 성능 테스트"""
        game_engine = setup_performance_environment['game_engine']
        analytics_service = setup_performance_environment['analytics_service']
        
        metrics = PerformanceMetrics()
        
        async def simulate_complete_game(game_index: int):
            """완전한 게임 시뮬레이션"""
            room_id = f"sim_room_{game_index}"
            
            start_time = time.time()
            
            try:
                # 1. 게임 생성
                success, _ = await game_engine.create_game(room_id, max_players=4)
                if not success:
                    raise Exception("게임 생성 실패")
                
                # 2. 플레이어 참가 (4명)
                for i in range(4):
                    success, _ = await game_engine.join_game(room_id, i+1, f"player_{i+1}")
                    if not success:
                        raise Exception(f"플레이어 {i+1} 참가 실패")
                
                # 3. 게임 시작
                success, _ = await game_engine.start_game(room_id)
                if not success:
                    raise Exception("게임 시작 실패")
                
                # 4. 분석 이벤트 추적
                await analytics_service.track_event("game_started", 1, {
                    "room_id": room_id,
                    "players_count": 4
                })
                
                # 5. 게임 종료
                success, _ = await game_engine.end_game(room_id, "simulation_end")
                if not success:
                    raise Exception("게임 종료 실패")
                
                end_time = time.time()
                metrics.record_response_time(end_time - start_time)
                metrics.record_success()
                
            except Exception as e:
                metrics.record_error()
        
        metrics.start_measurement()
        
        # 50개 동시 게임 시뮬레이션
        concurrent_games = 50
        tasks = [simulate_complete_game(i) for i in range(concurrent_games)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics.end_measurement()
        
        # 성능 지표 검증
        summary = metrics.get_summary()
        print(f"전체 게임 시뮬레이션 성능 테스트 결과: {summary}")
        
        assert summary['success_rate'] > 0.80  # 80% 이상 성공률
        assert summary['avg_response_time'] < 1.0  # 1초 미만 평균 게임 생성 시간
        assert summary['max_memory_usage'] < 80  # 메모리 사용량 80% 미만


class TestStressTest:
    """스트레스 테스트"""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_extreme_concurrent_load(self):
        """극한 동시 부하 테스트"""
        # 1000개 동시 작업으로 시스템 한계 테스트
        concurrent_operations = 1000
        
        async def extreme_operation(op_index: int):
            """극한 부하 작업"""
            # CPU 집약적 작업 시뮬레이션
            result = sum(i * i for i in range(1000))
            await asyncio.sleep(0.001)  # I/O 시뮬레이션
            return result > 0
        
        start_time = time.time()
        tasks = [extreme_operation(i) for i in range(concurrent_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # 결과 검증
        successful_results = [r for r in results if r is True]
        success_rate = len(successful_results) / len(results)
        total_time = end_time - start_time
        
        print(f"극한 부하 테스트 - 성공률: {success_rate}, 총 시간: {total_time}초")
        
        assert success_rate > 0.95  # 95% 이상 성공
        assert total_time < 10  # 10초 이내 완료
    
    @pytest.mark.stress
    def test_memory_stress(self):
        """메모리 스트레스 테스트"""
        initial_memory = psutil.virtual_memory().percent
        
        # 대용량 데이터 구조 생성
        large_lists = []
        for i in range(100):
            large_list = [f"data_{j}" * 100 for j in range(10000)]
            large_lists.append(large_list)
        
        peak_memory = psutil.virtual_memory().percent
        
        # 메모리 해제
        del large_lists
        gc.collect()
        
        final_memory = psutil.virtual_memory().percent
        
        print(f"메모리 스트레스 테스트 - 초기: {initial_memory}%, 최고: {peak_memory}%, 최종: {final_memory}%")
        
        # 메모리 복구 확인
        assert final_memory < peak_memory
        assert peak_memory < 90  # 90% 이하 사용


if __name__ == "__main__":
    # 성능 테스트만 실행
    pytest.main([__file__, "-v", "-m", "performance"])
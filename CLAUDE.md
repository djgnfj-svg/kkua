# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA) V2** is a real-time multiplayer Korean word-chain game. Built with Pure WebSocket architecture for real-time communication, featuring item systems, word validation, and game reporting.

## Tech Stack

### Backend
- **Python 3.11 + FastAPI** - Web framework
- **WebSocket** - Real-time communication
- **Redis** - Real-time state management (game sessions, cache)
- **PostgreSQL** - Persistent data storage
- **SQLAlchemy** - ORM
- **JWT + bcrypt** - Authentication/security
- **pytest** - Testing framework

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Zustand** - State management
- **TailwindCSS** - Styling
- **Native WebSocket** - Real-time communication
- **Vitest** - Testing framework

### Deployment
- **Docker Compose** - Container orchestration

## Architecture Overview

### WebSocket Communication Architecture
- **JWT Authentication**: Token extraction from headers on WebSocket connection
- **Connection Management**: User/room connection management via `connection_manager.py`
- **Message Routing**: Message type-specific handler branching in `message_router.py`
- **Game State**: Real-time game state synchronization through Redis

### State Management Layers
1. **React Zustand Stores**: Client UI state
2. **Redis Cache**: Real-time game state (24-hour TTL)
3. **PostgreSQL**: Persistent data (users, game history)

### Core Service Modules
- **game_engine.py**: Game logic, turn management, victory conditions
- **word_validator.py**: Korean word validation (10,794 KKuTu DB words) with 두음법칙 support
- **item_service.py**: Item system with distraction effects
- **redis_models.py**: Real-time game state models with JSON serialization

## Development Commands

### Docker Development (Recommended)
```bash
# Quick start (개발 환경)
./dev.sh

# Or manually
docker-compose up -d --build

# Start specific services only
docker-compose up -d db redis backend
docker-compose up -d frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Local Development
```bash
# Database only in Docker
docker-compose up -d db redis

# Backend dev server
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev server
cd frontend
npm install
npm run dev
```

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000
- **PostgreSQL**: localhost:5432 (postgres/password/kkua_db)
- **Redis**: localhost:6379

## Testing & Build Commands

### Frontend
```bash
# Lint check
npm run lint
# Or in Docker
docker-compose exec frontend npm run lint

# Type check
npx tsc -b
# Or in Docker
docker-compose exec frontend npx tsc -b

# Run tests
npm run test
# Or in Docker
docker-compose exec frontend npm run test

# Production build
npm run build
# Or in Docker
docker-compose exec frontend npm run build
```

### Backend
```bash
# Run tests
python -m pytest tests/ -v
# Or in Docker
docker exec kkua-backend-1 python -m pytest tests/ -v

# Test coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run specific test
python -m pytest tests/test_game_engine.py -v
python -m pytest tests/test_word_validator.py -v
python -m pytest tests/test_dueum_rules.py -v
```

## Debugging

### Log Monitoring
```bash
# Real-time log monitoring
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# 파일 로그 확인 (권장)
tail -f logs/kkua.log
cat logs/kkua.log | grep ERROR
cat logs/kkua.log | grep -E "(게스트 로그인|게임룸 생성|아이템 사용)"

# Redis monitoring
docker exec kkua-redis-1 redis-cli monitor

# Service status check
docker-compose ps
```

### Log Files
- **위치**: `./logs/kkua.log`
- **로테이션**: 50MB 단위로 3개 파일까지 보관
- **포맷**: `YYYY-MM-DD HH:MM:SS [레벨] 모듈명: 메시지`
- **레벨**: DEBUG, INFO, WARNING, ERROR
- **설정**: `LOG_LEVEL` 환경변수로 제어

### Database Access
```bash
# PostgreSQL access
docker exec -it kkua-db-1 psql -U postgres -d kkua_db

# Redis access
docker exec -it kkua-redis-1 redis-cli

# Clear Redis cache
docker exec kkua-redis-1 redis-cli FLUSHDB

# Import word data
docker exec kkua-backend-1 python scripts/init_data.py
```

## Coding Conventions

### Common Rules
- **Type Safety**: TypeScript strict mode, Python type hints required
- **Async Handling**: Consistent async/await patterns
- **Error Handling**: Handle all exceptions appropriately
- **Security**: User input validation, JWT token validation, SQL injection prevention
- **Performance**: Avoid unnecessary re-renders/DB queries

### Frontend (React + TypeScript)
- **Functional Components**: Use React hooks
- **State Management**: Zustand store patterns (`stores/useGameStore.ts`, `stores/useUserStore.ts`)
- **Styling**: TailwindCSS utility classes
- **WebSocket**: Custom hooks (`useWebSocket.ts`, `useNativeWebSocket.ts`)
- **Error Handling**: ErrorBoundary components

### Backend (Python)
- **Type Hints**: Type hints for all functions
- **Logging**: Structured logging via structlog
- **WebSocket**: Connection management through `connection_manager.py`
- **Game Logic**: Module separation in `services/`
- **Data Models**: SQLAlchemy ORM, Pydantic validation

## Key File Structure

### Backend Core Files
- `main.py`: FastAPI app entry point, CORS/auth middleware
- `websocket/connection_manager.py`: WebSocket connection management
- `websocket/message_router.py`: Message type-based routing
- `services/game_engine.py`: Game engine (turn management, victory conditions)
- `redis_models.py`: Redis game state models

### Frontend Core Files
- `src/stores/useGameStore.ts`: Game state management
- `src/hooks/useWebSocket.ts`: WebSocket connection hook
- `src/components/ui/`: Reusable UI components
- `src/pages/GameRoomPage.tsx`: Main game screen

## Current Status

**KKUA V2 Project Complete** ✅

### Completed Features
- ✅ Real-time multiplayer word-chain game
- ✅ JWT auth-based WebSocket communication
- ✅ Word card system (difficulty-based colors, animations)
- ✅ Player card UI (status display, score management)
- ✅ Item system (5 rarity levels + 방해 아이템)
- ✅ Visual distraction effects (고양이, 화면흔들기, 흐림, 낙하물, 색상반전)
- ✅ Game report and ranking system
- ✅ Responsive mobile design
- ✅ Auto-reconnect logic
- ✅ Docker container environment
- ✅ File logging system (개발/프로덕션)

### Production Deployment
```bash
# Quick local deployment
./deploy.sh
```
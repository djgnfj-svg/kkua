# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer Korean word-chain game. Built with Pure WebSocket architecture for real-time communication, featuring item systems, word validation, and game reporting.

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

### Infrastructure
- **Docker Compose** - Container orchestration
- **Nginx** - Reverse proxy and static file serving
- **Docker volumes** - Data persistence

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
- **word_validator.py**: Korean word validation (306,456 KKuTu DB words) with 두음법칙 support
- **item_service.py**: Item system with distraction effects
- **redis_models.py**: Real-time game state models with JSON serialization

## Development Commands

### Quick Start
```bash
# Development environment (starts all services)
./dev.sh

# Production deployment (prompts for domain if needed)
./prod.sh [domain]
```

### Development Environment
```bash
# Start all services (uses docker-compose.override.yml automatically)
docker-compose --env-file .env.dev up -d --build

# View logs
docker-compose --env-file .env.dev logs -f
docker-compose --env-file .env.dev logs -f backend  # Backend only
docker-compose --env-file .env.dev logs -f frontend # Frontend only

# Stop services
docker-compose --env-file .env.dev down

# Restart specific service
docker-compose --env-file .env.dev restart backend
```

### Production Environment
```bash
# Deploy with domain configuration
./prod.sh                      # Interactive domain setup
./prod.sh mydomain.com         # Direct domain specification

# Manual commands (uses docker-compose.prod.yml)
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs -f
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml down
docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml ps
```

### Environment Configuration

#### Development (.env.dev)
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws
- **Health Check**: http://localhost:8000/health

#### Production (.env.prod)
- **Frontend**: http://localhost (via Nginx)
- **API Docs**: http://localhost/api/docs
- **Health Check**: http://localhost/health
- **도메인 설정**: `./prod.sh`로 자동 설정 또는 .env.prod 직접 수정
- **보안**: HTTPS/WSS 지원, JWT 토큰 인증

### Service Ports
- **PostgreSQL**: 5432
- **Redis**: 6379
- **Backend**: 8000
- **Frontend**: 5173 (dev) / served by Nginx (prod)
- **Nginx**: 80 (prod)

## Testing & Build Commands

### Frontend Testing
```bash
# Run all tests
npm run test
docker-compose --env-file .env.dev exec frontend npm run test

# Run tests with UI
npm run test:ui

# Run specific test file
npm run test src/hooks/useWebSocket.test.ts

# Lint and type checking
npm run lint                    # ESLint
npx tsc -b                      # TypeScript type check
docker-compose --env-file .env.dev exec frontend npm run lint
docker-compose --env-file .env.dev exec frontend npx tsc -b

# Production build
npm run build
docker-compose --env-file .env.dev exec frontend npm run build
```

### Backend Testing
```bash
# Run all tests with coverage
python -m pytest tests/ -v
docker exec kkua-backend-1 python -m pytest tests/ -v

# Test coverage report
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run specific test files
python -m pytest tests/test_game_engine.py -v
python -m pytest tests/test_word_validator.py -v
python -m pytest tests/test_dueum_rules.py -v

# Run specific test function
python -m pytest tests/test_game_engine.py::test_game_start -v
```

## Debugging & Monitoring

### Log Monitoring
```bash
# Real-time container logs
docker-compose --env-file .env.dev logs -f          # All services
docker-compose --env-file .env.dev logs -f backend  # Backend only
docker-compose --env-file .env.dev logs -f frontend # Frontend only
docker-compose --env-file .env.dev logs --tail=100  # Last 100 lines

# File-based logs (production/development)
tail -f logs/kkua.log                              # Real-time log tail
tail -n 100 logs/kkua.log                         # Last 100 lines
cat logs/kkua.log | grep ERROR                    # Error filtering
cat logs/kkua.log | grep -E "(게스트 로그인|게임룸 생성|아이템 사용)"

# Redis monitoring
docker exec kkua-redis-1 redis-cli monitor        # Real-time Redis commands
docker exec kkua-redis-1 redis-cli --scan         # List all keys

# Container status
docker-compose --env-file .env.dev ps             # Service status
docker stats                                       # Resource usage
```

### Log Configuration
- **File Location**: `./logs/kkua.log`
- **Rotation**: 50MB per file, max 3 files
- **Format**: `YYYY-MM-DD HH:MM:SS [LEVEL] module: message`
- **Levels**: DEBUG, INFO, WARNING, ERROR (controlled by `LOG_LEVEL` env var)

### Database Operations
```bash
# PostgreSQL CLI access
docker exec -it kkua-db-1 psql -U postgres -d kkua_db

# Common PostgreSQL queries
\dt                    # List all tables
\d+ table_name        # Describe table structure
SELECT * FROM users;  # Query data

# Redis CLI access
docker exec -it kkua-redis-1 redis-cli

# Common Redis commands
KEYS *                # List all keys
GET key_name         # Get value
FLUSHDB              # Clear all data (caution!)
INFO                 # Server information

# Database initialization
docker exec kkua-backend-1 python scripts/init_data.py  # Import word data
docker exec kkua-backend-1 python scripts/wait-for-db.sh # Check DB connection
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

## Project Structure

### Backend Core Modules
- `main.py`: FastAPI app entry, middleware configuration
- `auth.py`: JWT authentication and user management
- `websocket/`:
  - `connection_manager.py`: WebSocket connection lifecycle
  - `message_router.py`: Message type routing and handling
  - `handlers.py`: Business logic for each message type
- `services/`:
  - `game_engine.py`: Core game logic, turn management
  - `word_validator.py`: Korean word validation with 두음법칙
  - `item_service.py`: Item system and effects
- `models/`: SQLAlchemy database models
- `redis_models.py`: Redis cache models
- `scripts/`:
  - `init_data.py`: Database initialization and word data import
  - `healthcheck.py`: Service health verification

### Frontend Core Modules
- `src/stores/`:
  - `useGameStore.ts`: Game state management
  - `useUserStore.ts`: User authentication state
- `src/hooks/`:
  - `useWebSocket.ts`: WebSocket connection management
  - `useNativeWebSocket.ts`: Native WebSocket implementation
- `src/components/`:
  - `ui/`: Reusable UI components (Button, Card, Input, etc.)
  - `game/`: Game-specific components
- `src/pages/`: Main application pages
- `src/services/`: API service layer

### Configuration Files
- `nginx/nginx.dev.conf`: Development reverse proxy (proxies to frontend dev server)
- `nginx/nginx.prod.conf`: Production reverse proxy + static file serving
- `docker-compose.override.yml`: Development-specific overrides (auto-loaded)
- `docker-compose.prod.yml`: Production-specific overrides

## Common Development Tasks

### Container Management
```bash
# Clean rebuild (when dependencies change)
docker-compose --env-file .env.dev down -v
docker-compose --env-file .env.dev up -d --build

# Access container shell
docker exec -it kkua-backend-1 bash
docker exec -it kkua-frontend-1 sh
docker exec -it kkua-db-1 bash

# Clean up Docker resources
docker system prune -a              # Remove unused containers/images
docker volume prune                 # Remove unused volumes
```

### Troubleshooting
```bash
# Check service health
curl http://localhost:8000/health  # Backend health
docker-compose --env-file .env.dev ps

# Reset database
docker-compose --env-file .env.dev down -v
docker-compose --env-file .env.dev up -d
docker exec kkua-backend-1 python scripts/init_data.py

# Clear Redis cache only
docker exec kkua-redis-1 redis-cli FLUSHDB

# Fix permission issues
sudo chown -R $USER:$USER .
```

## WebSocket Message Types

### Client → Server
- `join_room`: Join game room
- `leave_room`: Leave current room
- `submit_word`: Submit word in game
- `use_item`: Use an item
- `game_action`: Various game actions (start, ready, etc.)

### Server → Client
- `room_update`: Room state changes
- `game_update`: Game state updates
- `word_submitted`: Word submission result
- `item_used`: Item usage notification
- `error`: Error messages

## Current Project Status

**KKUA Project Complete** ✅

### Core Features
- ✅ Real-time multiplayer Korean word-chain game
- ✅ JWT-based WebSocket authentication
- ✅ Word validation with 두음법칙 support (306,456 words)
- ✅ 5-tier item system with visual distraction effects
- ✅ Game statistics and ranking system
- ✅ Auto-reconnection with state recovery
- ✅ Responsive design for mobile/desktop
- ✅ File-based logging with rotation
- ✅ Docker containerized deployment
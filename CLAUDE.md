# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer Korean word chain game (끝말잇기) with dual-architecture data management (PostgreSQL + Redis), FastAPI backend, and React frontend. The game features advanced mechanics including items, multiple game modes, friend system, and sophisticated scoring.

## Quick Start Commands

```bash
# Setup environment (first time only)
cp backend/.env.example backend/.env

# Start development environment
docker-compose up -d

# Start with frontend
docker-compose --profile frontend up -d

# Stop services
docker-compose down
docker-compose down -v  # Also removes data volumes

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [backend|frontend|db|redis]
```

## Development Commands

### Backend Testing & Quality
```bash
# Run all tests with coverage
docker exec kkua-backend-1 python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
docker exec kkua-backend-1 python -m pytest tests/services/test_gameroom_service.py -v

# Run tests matching pattern
docker exec kkua-backend-1 python -m pytest tests/ -k "test_create" -v

# Code quality
docker exec kkua-backend-1 ruff check . --fix
docker exec kkua-backend-1 ruff format .

# Run tests via test service
docker-compose run --rm backend-test
```

### Frontend Testing & Quality
```bash
# Run tests with coverage (70% threshold)
docker exec kkua-frontend-1 npm run test:coverage

# Run tests in watch mode
docker exec kkua-frontend-1 npm run test:watch

# Build for production
docker exec kkua-frontend-1 npm run build

# Code formatting
docker exec kkua-frontend-1 npx prettier --write "src/**/*.{js,jsx}"
docker exec kkua-frontend-1 npx eslint --fix "src/**/*.{js,jsx}"
```

### Database Operations
```bash
# Access PostgreSQL
docker exec -it kkua-db-1 psql -U postgres -d mydb

# Access Redis
docker exec kkua-redis-1 redis-cli

# Monitor Redis commands
docker exec kkua-redis-1 redis-cli monitor

# Clear Redis cache
docker exec kkua-redis-1 redis-cli FLUSHDB

# Run database migrations
docker-compose --profile migrate run --rm backend-migrate
```

## Architecture: Dual Data Management

### PostgreSQL (Persistent Storage)
- User accounts and sessions
- Game room metadata
- Game logs and historical data
- Friend relationships with status tracking (pending/accepted/blocked/rejected)
- Item system with rarities (common/uncommon/rare/epic/legendary) and types
- Player profiles and game statistics
- Game modes and configurations
- Permanent statistics and leaderboards

### Redis (Real-time State)
- Active game state with 24-hour TTL
- Turn timers and countdown management
- Word chain validation
- Real-time player statistics
- WebSocket message routing

### Key Services

**Backend Core Services:**
- `redis_game_service.py`: Real-time game state management with async timers
- `game_data_persistence_service.py`: Syncs Redis game results to PostgreSQL
- `session_service.py`: Thread-safe in-memory session storage with auto-cleanup
- `websocket_message_service.py`: WebSocket message processing and routing
- `advanced_score_service.py`: Speed bonuses, combos, word rarity scoring
- `friendship_service.py`: Friend system with requests, blocking, and status management
- `item_service.py`: Game items and power-ups with different rarities and effects
- `game_mode_service.py`: Multiple game modes with varying rules and mechanics

**Frontend Architecture:**
- Pages have dedicated `components/` and `hooks/` subdirectories
- Zustand for state management with localStorage persistence
- TailwindCSS for styling and responsive design
- `useGameRoomSocket.js`: WebSocket with exponential backoff reconnection
- Toast notifications for user feedback
- Error boundary handling with proper fallback UI

## API Patterns

### Authentication Flow
1. `POST /auth/login` with nickname → creates/retrieves guest account
2. Session token stored in HTTP-only cookie
3. All requests include session cookie
4. WebSocket validates session from cookie headers

### Game Flow
1. Create/join room via REST API
2. WebSocket connection for real-time updates
3. Game state managed in Redis during play
4. Results persisted to PostgreSQL after game ends

### WebSocket Messages
- URL: `ws://localhost:8000/ws/gamerooms/{room_id}`
- Authentication: Session cookie required
- Key events: `game_started_redis`, `word_submitted`, `game_time_update`, `game_over`
- Connection validates session from cookie headers

## Testing Strategy

### Backend Tests
- Structure mirrors source code in `backend/tests/`
- Uses pytest with fixtures in `conftest.py`
- Test layers: models/ → repositories/ → services/ → integration
- Comprehensive test coverage for all new features (friendship, items, game modes)
- Mock Redis and PostgreSQL connections for isolated testing
- Coverage target: Comprehensive unit and integration tests
- CI runs: `python -m pytest tests/ -v --tb=short`

### Frontend Tests
- Jest + React Testing Library
- Coverage thresholds: 70% for all metrics
- CI runs: `npm test -- --watchAll=false --passWithNoTests`

## Environment Configuration

### Key Backend Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string  
- `SECRET_KEY`: Session encryption key (change in production!)
- `ENVIRONMENT`: development | production | testing
- `CORS_ORIGINS`: Comma-separated allowed origins
- `SESSION_TIMEOUT`: Default 86400 (24 hours)

### Key Frontend Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_WS_URL`: WebSocket URL
- `CHOKIDAR_USEPOLLING`: true (for Docker file watching)

## CI/CD Pipeline

### GitHub Actions Workflows
1. **ci.yml**: Runs tests on push/PR to main/develop
   - PostgreSQL and Redis services auto-configured
   - Backend: Python 3.11, pytest
   - Frontend: Node.js 18, npm test
   - Docker build test on push

2. **pr-checks.yml**: Validates branch naming conventions
   - Checks for: feature/, fix/, hotfix/, release/, docs/

3. **deploy.yml**: Auto-deploy on push to main
   - Requires secrets: DEPLOY_HOST, DEPLOY_USER, DEPLOY_KEY

## Common Development Tasks

### Adding New Features
1. **Backend API**: Schema → Model → Repository → Service → Router → Tests
   - Models define database schema with SQLAlchemy (enums for statuses/types)
   - Repositories handle database operations with error handling
   - Services contain business logic and validation  
   - Routers expose FastAPI endpoints with Pydantic schemas
2. **Frontend Feature**: Page/components → hooks → API calls → State management
3. **WebSocket**: Add message type to `websocket_message_service.py` and frontend hook
4. **New Models**: Follow existing patterns with enums, relationships, and proper indexing
5. **Database Changes**: Use Alembic for migrations, test in development first

### Debugging Issues
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/docs  # API documentation

# View container logs
docker-compose logs -f [service_name]

# Database inspection
docker exec -it kkua-db-1 psql -U postgres -d mydb

# Redis monitoring
docker exec kkua-redis-1 redis-cli monitor

# Reset everything (WARNING: deletes data)
docker-compose down -v && docker-compose up -d
```

## Key Files to Know

### Backend
- `main.py`: FastAPI app with router registration
- `app_config.py`: Environment-based configuration
- `services/redis_game_service.py`: Core game logic
- `websocket/connection_manager.py`: WebSocket facade
- `middleware/auth_middleware.py`: Session validation
- `middleware/csrf_middleware.py`: CSRF protection for forms
- `middleware/rate_limiter.py`: Rate limiting for API and WebSocket endpoints
- `config/sentry_config.py`: Error tracking and monitoring utilities  
- `config/logging_config.py`: Centralized logging configuration

### Frontend  
- `App.js`: Main routing configuration
- `hooks/useGameRoomSocket.js`: WebSocket connection management
- `store/guestStore.js`: User state management
- `contexts/ToastContext.js`: Global notifications

## Production Deployment

```bash
# Setup production config
cp backend/.env.example backend/.env
# Edit with production values (change SECRET_KEY, set ENVIRONMENT=production)

# Deploy backend only (typical production setup)
ENVIRONMENT=production docker-compose up -d backend db redis

# Or deploy with frontend
ENVIRONMENT=production docker-compose --profile frontend up -d

# Production deployment features:
# - Environment variables for production
# - Multi-worker uvicorn for backend
# - Production security configurations
```
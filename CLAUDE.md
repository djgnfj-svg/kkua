# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer Korean word chain game (끝말잇기) with advanced features including item mechanics, multiple game modes, friend system, and sophisticated scoring. Built with FastAPI backend, PostgreSQL + Redis for dual-architecture data management, and React frontend with TailwindCSS.


## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd kkua

# One-click deployment (automatically creates .env)
./deploy.sh              # Development
./deploy.sh production   # Production

# Verify services are running
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/        # Frontend (development only)

# View logs
./scripts/logs.sh development backend   # Backend logs
./scripts/logs.sh development frontend  # Frontend logs

# Run tests
docker-compose run --rm backend-test
```

## Development Commands

### Docker Environment
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Rebuild specific service
docker-compose build [backend|frontend|db|redis]

# Quick deployment scripts
./deploy.sh              # Deploy development
./stop.sh                # Stop development
./scripts/status.sh      # Check service status
```

### Backend Development
```bash
# Run tests
docker exec kkua-backend-1 python -m pytest tests/ -v

# Run specific test file
docker exec kkua-backend-1 python -m pytest tests/services/test_gameroom_service.py -v

# Code linting and formatting
docker exec kkua-backend-1 ruff check . --fix
docker exec kkua-backend-1 ruff format .
```

### Frontend Development
```bash
# Run tests
docker exec kkua-frontend-1 npm test

# Run tests with coverage
docker exec kkua-frontend-1 npm test -- --coverage --watchAll=false

# Code formatting
docker exec kkua-frontend-1 npx prettier --write src/**/*.js

# Linting
docker exec kkua-frontend-1 npx eslint --fix src/**/*.js
```

### Database Operations
```bash
# Access PostgreSQL
docker exec -it kkua-db-1 psql -U postgres -d mydb
```

## Production Deployment

```bash
# Setup production environment
cp backend/.env.production.example backend/.env.production
# Edit backend/.env.production with production values

# Deploy production
./deploy.sh production

# Stop production
./stop.sh production

# Check production status
./scripts/status.sh production

# Manual production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## Architecture Overview

### Backend Structure (FastAPI)
- **main.py**: Application entry point with router registration and CORS setup
- **app_config.py**: Environment-based configuration management
- **models/**: SQLAlchemy models for database entities
  - `gameroom_model.py`: Game room and participant models with status enums
  - `guest_model.py`: Guest/user model with UUID and session token support
  - `game_log_model.py`: Game result tracking with comprehensive statistics
  - `player_game_stats_model.py`: Individual player statistics per game
  - `word_chain_entry_model.py`: Word chain entry tracking
- **routers/**: API endpoint definitions
  - `auth_router.py`: Authentication endpoints for session management
  - `gamerooms_router.py`: Basic CRUD operations for game rooms
  - `gameroom_actions_router.py`: Game room actions (join, leave, ready, start)
  - `gameroom_ws_router.py`: WebSocket functionality for real-time communication
  - `game_api_router.py`: Redis-based game API endpoints (word submission, game state)
  - `guests_router.py`: Guest management endpoints with session support
  - `csrf_router.py`: CSRF token endpoints for security
  - `game_mode_router.py`: Game mode management endpoints
  - `item_router.py`: Item management and purchase endpoints
  - `friendship_router.py`: Friend system endpoints
- **services/**: Business logic layer
  - `auth_service.py`: Authentication, session management, and cookie handling
  - `gameroom_service.py`: Consolidated game room management and actions logic
  - `guest_service.py`: Guest management logic
  - `session_service.py`: Thread-safe in-memory session storage with automatic cleanup
  - `game_state_service.py`: Game state management and word chain validation
  - `websocket_message_service.py`: WebSocket message processing and routing
  - `redis_game_service.py`: Redis-based real-time game state management
  - `game_data_persistence_service.py`: Critical service for persisting game results from Redis to PostgreSQL
  - `advanced_score_service.py`: Advanced scoring system with speed bonuses, combos, and word rarity
  - `item_service.py`: Item management and effects for gameplay
  - `game_mode_service.py`: Game mode configuration and management
  - `friendship_service.py`: Friend system management
- **schemas/**: Pydantic models for request/response validation
  - `auth_schema.py`: Authentication request/response models
  - `gameroom_schema.py`: Game room data models
  - `gameroom_actions_schema.py`: Game room action models
  - `gameroom_ws_schema.py`: WebSocket message models
  - `websocket_schema.py`: Enhanced WebSocket message validation
  - `guest_schema.py`: Guest/user data models
  - `game_mode_schema.py`: Game mode configuration models
  - `item_schema.py`: Item definition and usage models
  - `friendship_schema.py`: Friend request and relationship models
  - `player_profile_schema.py`: Extended player profile models
- **middleware/**: Custom middleware components
  - `auth_middleware.py`: Session-based authentication with secure cookie validation
  - `exception_handler.py`: Global exception handling middleware
  - `rate_limiter.py`: Rate limiting for API endpoints
  - `csrf_middleware.py`: CSRF protection middleware for state-changing operations
  - `logging_middleware.py`: Request/response logging middleware for audit trails
  - `security_headers_middleware.py`: Security headers middleware (HSTS, CSP, etc.)
- **websocket/**: WebSocket connection management
  - `connection_manager.py`: Game room WebSocket facade with dual architecture support
  - `websocket_manager.py`: Low-level WebSocket connection management
  - `word_chain_manager.py`: Legacy word chain game engine (superseded by Redis service)
- **utils/**: Utility modules
  - `security.py`: Security utilities for session token generation and validation
- **repositories/**: Data access layer with database operations
  - `gameroom_repository.py`: Game room and participant data access
  - `guest_repository.py`: Guest/user data access
  - `game_log_repository.py`: Game result and statistics data access
  - `player_profile_repository.py`: Player profile and statistics access
  - `friendship_repository.py`: Friend relationships data access
- **db/**: Database configuration and setup
  - `postgres.py`: PostgreSQL database connection and session management
- **config/**: Configuration files for cookies, logging, etc.
  - `cookie.py`: Cookie configuration settings
  - `logging_config.py`: Comprehensive logging setup with multiple log files
  - `sentry_config.py`: Sentry error tracking configuration
- **tests/**: Comprehensive test suite mirroring source code structure
  - `conftest.py`: Test configuration and fixtures
  - `models/`: Model testing
  - `repositories/`: Data access layer testing  
  - `services/`: Business logic testing
- **logs/**: Application logging directory
  - `kkua.log`: General application logs
  - `error.log`: Error-specific logging
  - `audit.log`: Security and audit trail
  - `performance.log`: Performance monitoring
  - `security.log`: Security-related events

### Frontend Structure (React)
- **src/Pages/**: Main application pages with modular component structure
  - Each page has its own `components/` and `hooks/` subdirectories
  - `Loading/`: Initial loading/welcome page with modal components
  - `Lobby/`: Game room lobby with room list and creation
    - `components/GameModeSelector.js`: Game mode selection component
  - `GameLobbyPage/`: Individual game room lobby with chat and participant management
  - `InGame/`: Active game interface with word chain gameplay
    - `components/ItemPanel.js`: Item selection and usage panel
    - `components/ScoreDisplay.js`: Real-time score display
  - `GameResult/`: Game results and statistics display page
    - `components/AdvancedPlayerRanking.js`: Enhanced ranking with detailed stats
  - `NotFound/`: 404 error page for invalid routes
- **src/store/**: Zustand state management
  - `guestStore.js`: Guest authentication and session management
  - `guestStore.test.js`: Store unit tests
- **src/Api/**: API communication layer
  - `axiosInstance.js`: Configured axios client with interceptors
  - `authApi.js`: Authentication API calls (login, logout, profile)
  - `roomApi.js`: Game room API calls
  - `userApi.js`: User/guest API calls
  - `wsUrl.js`: WebSocket URL configuration
  - `gameModeApi.js`: Game mode API calls
  - `itemApi.js`: Item management API calls
- **src/components/**: Shared utility components
  - `LoadingSpinner.js`: Loading indicator component
  - `ProtectedRoute.js`: Route protection wrapper
  - `WebSocketStatus.js`: WebSocket connection status indicator with reconnection progress
  - `Toast.js`: Toast notification component for user feedback
- **src/contexts/**: React context providers
  - `AuthContext.js`: Authentication context for user state
  - `ToastContext.js`: Global toast notification system with success/error/warning/info types
- **src/utils/**: Shared utilities
  - `socket.js`: WebSocket connection management
  - `urls.js`: URL configuration
  - `cacheManager.js`: Client-side caching utilities
  - `errorMessages.js`: Centralized error message handling
  - `userIsTrue.js`: User validation utilities
- **src/hooks/**: Custom React hooks
  - `useGameRoomSocket.js`: Enhanced WebSocket hook with exponential backoff reconnection, connection state tracking, and toast notifications

### Database Schema
- **guests**: User/guest management with guest_id, UUID, nickname, and session tracking
- **gamerooms**: Game room information with status tracking and owner reference
- **gameroom_participants**: Many-to-many relationship between guests and game rooms with ready status
- **game_logs**: Game session records with duration, winner, and statistics
- **word_chain_entries**: Individual word entries with player and timing data
- **player_game_stats**: Detailed per-player statistics for each game
- **game_modes**: Different game mode configurations (classic, speed, item)
- **items**: Game items with effects and costs
- **friendships**: Friend relationships between players
- **player_profiles**: Extended player profiles with stats and achievements

### Key Architectural Patterns
1. **Layered Architecture**: Controllers (routers) → Services → Repositories → Models
2. **Component-Based Frontend**: Each page is broken down into reusable components with custom hooks
3. **Real-time Communication**: WebSocket connections for live game updates and chat
4. **State Management**: Zustand for client-side state with localStorage persistence
5. **Session-based Authentication**: Secure cookie-based session management replacing UUID-based system
6. **Middleware Pattern**: Authentication middleware for protecting routes and validating sessions
7. **Environment-based Configuration**: Separate settings for development and production
8. **Single Responsibility Principle**: Recent refactoring split large components into focused services
9. **Dual Game State Architecture**: PostgreSQL for persistent data + Redis for real-time game state
10. **Performance Optimization**: Client-side timer synchronization with server validation

## Redis Architecture & Real-time Game Management

### Redis Game Service Architecture
The **RedisGameService** (`backend/services/redis_game_service.py`) provides high-performance, real-time game state management:

#### Core Features:
- **Real-time Game State**: Game state stored in Redis with 24-hour TTL
- **Turn-based Timer Management**: Async timer system with WebSocket broadcasts
- **Player Statistics**: Individual player performance tracking per game
- **Word Validation**: Korean word validation with duplicate checking
- **Automatic Game Flow**: Turn progression and round management

#### Redis Data Structure:
```bash
# Game state
game:{room_id}                    # Main game state JSON
game:{room_id}:player:{guest_id}  # Individual player stats
```

#### Key Redis Operations:
- **Game Creation**: Shuffled participant order with random first player
- **Word Submission**: Real-time validation and state updates
- **Timer Management**: Async countdown with critical moment broadcasts
- **Game Statistics**: Score calculation and performance tracking

### Dual Architecture Pattern
The application uses a sophisticated dual architecture for optimal performance:

#### PostgreSQL (Persistent Storage):
- Game room metadata and participant relationships
- User session management and authentication
- Game logs and historical statistics
- Permanent data requiring ACID compliance

#### Redis (Real-time State):
- Active game state and current player information
- Turn timers and countdown management
- Word chain validation and used words tracking
- Real-time player statistics during gameplay

### WebSocket Integration
Redis game events automatically trigger WebSocket broadcasts:
- **Game Start**: `game_started_redis` with participant order
- **Word Submission**: `word_submitted` with next player information
- **Timer Updates**: `game_time_update` for real-time countdown
- **Game Over**: `game_over` with final results

### Performance Optimizations
1. **Client-side Timer**: Reduces server load with local countdown synchronization
2. **Selective Broadcasting**: Timer updates only at critical moments (10, 5, 3, 2, 1 seconds)
3. **Connection Pooling**: Redis client with optimized connection management
4. **Session Cleanup**: Automatic expired session removal with threading

## Testing Strategy

### Backend Tests
- **Unit Tests**: Located in `backend/tests/` with structure mirroring source code
- **Test Categories**:
  - Model tests: Database entity validation
  - Repository tests: Data access layer testing
  - Service tests: Business logic validation
  - Integration tests: API endpoint testing

### Running Tests
```bash
# Run all backend tests
docker exec kkua-backend-1 python -m pytest tests/ -v

# Run tests with coverage
docker exec kkua-backend-1 python -m pytest tests/ --cov=. --cov-report=html

# Run tests with XML coverage report (for CI/CD)
docker exec kkua-backend-1 python -m pytest tests/ --cov=. --cov-report=xml

# Use the dedicated test service (runs tests and exits)
docker-compose run --rm backend-test

# Run specific test file
docker exec kkua-backend-1 python -m pytest tests/services/test_gameroom_service.py -v

# Run tests matching a pattern
docker exec kkua-backend-1 python -m pytest tests/ -k "test_create" -v

# Frontend tests
docker exec kkua-frontend-1 npm test -- --passWithNoTests
docker exec kkua-frontend-1 npm test -- --coverage --watchAll=false

# Frontend build for production
docker exec kkua-frontend-1 npm run build

# Run tests for specific service or module
docker exec kkua-backend-1 python -m pytest tests/services/test_redis_game_service.py -v
docker exec kkua-backend-1 python -m pytest tests/ -k "redis" -v  # Test pattern matching
```

## WebSocket Implementation

### Game Room WebSocket
- **URL**: `ws://localhost:8000/ws/gamerooms/{room_id}`
- **Purpose**: Real-time game room updates, chat, and game state synchronization
- **Message Types**: Join/leave notifications, ready status updates, chat messages, game actions
- **Authentication**: Session-based authentication via cookies (session_token required)
- **Architecture**: Simplified router with separate WebSocketMessageService for message processing

## API Documentation

### Key API Endpoints

#### Authentication
- `POST /auth/login` - Login with nickname
- `POST /auth/logout` - Logout and clear session
- `GET /auth/me` - Get current user profile (requires auth)
- `PUT /auth/me` - Update user profile (requires auth)
- `GET /auth/status` - Check authentication status

#### Game Rooms
- `GET /gamerooms` - List all game rooms
- `POST /gamerooms` - Create new game room (requires auth)
- `GET /gamerooms/{room_id}` - Get room details
- `DELETE /gamerooms/{room_id}` - Delete room (owner only)

#### Game Room Actions
- `POST /gamerooms/{room_id}/join` - Join a game room
- `POST /gamerooms/{room_id}/leave` - Leave a game room
- `POST /gamerooms/{room_id}/ready` - Toggle ready status
- `POST /gamerooms/{room_id}/start` - Start game (owner only)

#### Guests/Users
- `GET /guests` - List all guests
- `GET /guests/{guest_id}` - Get guest details

#### Game Modes
- `GET /game-modes` - List available game modes
- `GET /game-modes/{mode_id}` - Get specific mode details

#### Items
- `GET /items` - List all available items
- `POST /items/use` - Use an item during gameplay

#### Friends
- `GET /friends` - Get friend list
- `POST /friends/request` - Send friend request
- `POST /friends/accept/{request_id}` - Accept friend request

### API Response Format
All API responses follow a consistent format:
```json
{
  "status": "success|error",
  "data": {}, // Response data
  "message": "Optional message"
}
```

### Error Responses
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Accessing API Documentation
- Development: FastAPI automatic docs at `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Git Workflow

### Branch Structure (Git Flow)
- **main**: Production-ready code
- **develop**: Development integration branch
- **feature/***: Feature development branches
- **release/***: Release preparation branches
- **hotfix/***: Emergency fixes for production

### Commit Message Convention
- **feat**: New feature
- **fix**: Bug fix
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **docs**: Documentation changes
- **chore**: Maintenance tasks


## Environment Variables

### Backend Environment Variables
- **DATABASE_URL**: PostgreSQL connection string
  - Development: `postgresql://postgres:mysecretpassword@db:5432/mydb`
  - Production: Use your production database URL
- **REDIS_URL**: Redis connection string
  - Development: `redis://redis:6379/0`
  - Production: Use your production Redis URL
- **SECRET_KEY**: Secret key for session management (change in production)
- **HOST**: Server host (default: `0.0.0.0`)
- **PORT**: Server port (default: `8000`)
- **DEBUG**: Enable debug mode (default: `True` for dev, `False` for prod)
- **ENVIRONMENT**: Current environment (`development`, `production`, `testing`)
- **CORS_ORIGINS**: List of allowed origins for CORS
  - Development: `["http://localhost:3000", "http://127.0.0.1:3000"]`
  - Production: Add your production domain
- **TESTING**: Set to `true` when running tests
- **SESSION_TIMEOUT**: Session timeout in seconds (default: 86400 = 24 hours)
- **SESSION_SECURE**: Enable secure cookies for HTTPS (default: `false` for dev)
- **SESSION_SAMESITE**: Cookie SameSite policy (`lax`, `strict`, or `none`)
- **ENABLE_SECURITY_HEADERS**: Enable security headers middleware
- **HSTS_MAX_AGE**: HSTS max age in seconds for production
- **SENTRY_DSN**: Sentry error tracking DSN (optional)
- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)

### Frontend Environment Variables
- **REACT_APP_API_URL**: Backend API URL (default: `http://localhost:8000`)
- **REACT_APP_WS_URL**: WebSocket URL (default: `ws://localhost:8000`)
- **REACT_APP_WS_BASE_URL**: WebSocket base URL for dynamic connection (fallback: `ws://localhost:8000`)
- **CHOKIDAR_USEPOLLING**: Enable polling for file watching in Docker (set to `true`)

### Docker Environment
- **POSTGRES_USER**: Database user (default: `postgres`)
- **POSTGRES_PASSWORD**: Database password (default: `mysecretpassword`)
- **POSTGRES_DB**: Database name (default: `mydb`)

### Redis Configuration
- **Image**: `redis:7-alpine`
- **Port**: `6379`
- **Persistence**: Volume mounted at `/data`
- **Health Check**: Uses `redis-cli ping` command

## Authentication System

### Session-Based Authentication
- **Login Endpoint**: `POST /auth/login` - Creates or retrieves guest account with nickname
- **Logout Endpoint**: `POST /auth/logout` - Clears session and cookies
- **Profile Endpoint**: `GET /auth/me` - Gets current user profile (requires authentication)
- **Update Profile**: `PUT /auth/me` - Updates user nickname
- **Auth Status**: `GET /auth/status` - Checks current authentication status

### Authentication Flow
1. Client sends login request with nickname
2. Server creates/retrieves guest account and generates session token
3. Session token stored in secure HTTP-only cookie
4. All subsequent requests include session cookie
5. WebSocket connections validate session from cookie headers
6. Middleware validates session for protected endpoints

## Common Development Patterns

### Adding New API Endpoints
1. Create schema in `backend/schemas/`
2. Add repository methods in `backend/repositories/`
3. Implement service logic in `backend/services/`
4. Create router endpoints in `backend/routers/`
5. Write tests in `backend/tests/`

### Adding New Frontend Features
1. Create page components in `src/Pages/[PageName]/components/`
2. Extract logic into custom hooks in `src/Pages/[PageName]/hooks/`
3. Add API calls in `src/Api/`
4. Update state management in `src/store/` if needed
5. Add routing in `src/App.js`

### WebSocket Integration
1. Use `websocket/connection_manager.py` for backend WebSocket handling
2. Implement frontend WebSocket logic in custom hooks
3. Handle connection lifecycle (connect, disconnect, reconnect)
4. Manage message routing and state updates

## Security Considerations

- Environment-based CORS configuration
- Session-based authentication with secure HTTP-only cookies
- Secure WebSocket connections with session validation
- Production-ready Nginx configuration with security headers
- Environment variable management for sensitive data
- CSRF protection for state-changing operations

### Important Security Notes
- **Never commit sensitive data**: Ensure `.env` files and API tokens are not committed to version control
- **MCP Configuration**: The `.mcp.json` file contains GitHub personal access tokens - ensure this file is in `.gitignore` for production
- **Session Security**: Always use HTTPS in production with `SESSION_SECURE=true`
- **Database Passwords**: Use strong, unique passwords for production databases
- **API Rate Limiting**: Rate limiting middleware is implemented for API protection
- **Production Settings**: Always review `backend/.env.production` before deployment

## Common Issues

### Docker Issues
```bash
# Check container logs
docker-compose logs [service]

# Restart services
docker-compose restart [service]

# Rebuild if dependencies changed
docker-compose build [service]

# Reset database (deletes all data)
docker-compose down -v && docker-compose up -d
```

### WebSocket Issues
- Check backend health: `curl http://localhost:8000/health`
- Verify session cookie in browser DevTools
- Check WebSocket URL: `ws://localhost:8000` for development
- Monitor reconnection in browser console

### Database Issues
```bash
# Check database logs
./scripts/logs.sh development db

# Access database directly
docker exec -it kkua-db-1 psql -U postgres -d mydb

# Reset database (WARNING: deletes all data!)
./stop.sh development --with-data
./deploy.sh
```

### Redis Issues  
```bash
# Check Redis connection
docker exec kkua-redis-1 redis-cli ping

# Monitor Redis commands
docker exec kkua-redis-1 redis-cli monitor

# Clear Redis cache
docker exec kkua-redis-1 redis-cli FLUSHDB
```


## Key Development Patterns

### Dual Architecture Pattern
- **Redis**: Real-time game state, timers, temporary data (<24h)
- **PostgreSQL**: User accounts, game logs, persistent relationships
- **WebSocket**: Real-time communication with exponential backoff reconnection
- **Session-based Auth**: HTTP-only cookies with middleware validation

### Performance Optimization
- Client-side timer synchronization with server validation
- Selective WebSocket broadcasts at critical moments
- Toast notifications for connection feedback
- Retry logic for data integrity

### New Features Architecture
- **Game Modes**: Configurable game modes with different rules and scoring
- **Item System**: Purchase and use items during gameplay for strategic advantages
- **Friend System**: Social features with friend requests and friend-only rooms
- **Advanced Scoring**: Speed bonuses, combo multipliers, word rarity scoring
- **Player Profiles**: Extended profiles with statistics and achievements

## Deployment Scripts

### Main Scripts
- **deploy.sh**: Main deployment script with environment support
- **stop.sh**: Stop services with optional data cleanup
- **scripts/status.sh**: Check service health and status
- **scripts/logs.sh**: View logs with service and environment filtering
- **scripts/backup/**: Database backup and restore utilities

### Script Usage
```bash
# Deploy with environment
./deploy.sh [development|production]

# Stop with data cleanup
./stop.sh [environment] [--with-data]

# Check specific service logs
./scripts/logs.sh [environment] [service] [--follow]

# Service status
./scripts/status.sh [environment]
```
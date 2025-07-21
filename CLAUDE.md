# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer word chain game (끝말잇기) with item mechanics. The project uses a FastAPI backend with PostgreSQL database and a React frontend with TailwindCSS for styling.

### Recent Updates
- **Connection UX Improvements**: Enhanced WebSocket reliability and user feedback
  - Exponential backoff reconnection (2s → 4s → 8s → 16s → 32s delays)
  - Increased retry attempts from 3 to 5 with visual progress indicators
  - Toast notification system for connection events with contextual messaging
  - Manual reconnection capability with enhanced WebSocketStatus component
- **Game Result Data Reliability**: Fixed 0-score display issues and improved data retrieval
  - Retry logic for incomplete Redis data processing
  - Backend data validation with fallback mechanisms
  - Enhanced error handling for game result edge cases
- **Code Quality**: Complete codebase cleanup and comment optimization
  - Removed 20+ legacy files and unused components
  - Cleaned unnecessary debug comments and console.log statements
  - Standardized code documentation with focus on 'why' over 'what'
- **Authentication System**: Migrated from UUID-based to secure session-based authentication with HTTP-only cookies
- **Redis Integration**: Implemented Redis-based real-time game state management
  - Real-time word chain game processing with turn timers
  - Session-based game state persistence (24-hour TTL)
  - Performance optimization through centralized state management
- **Backend Refactoring**: Consolidated services following Single Responsibility Principle
  - Merged GameroomActions into GameroomService
  - Split ConnectionManager into focused components
  - Introduced WebSocketMessageService for message handling
  - Added RedisGameService for high-performance game state management
- **Performance Optimizations**: Client-side timer synchronization and reduced WebSocket broadcasts

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd kkua
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Verify services are running
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/        # Frontend

# View logs
docker-compose logs -f

# Run tests
docker-compose run --rm backend-test
```

## Development Commands

### Docker Environment (Primary Development Method)
```bash
# Start all services (backend, frontend, database)
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build [backend|frontend|db]

# Access backend container shell
docker exec -it kkua-backend-1 /bin/bash

# Access frontend container shell
docker exec -it kkua-frontend-1 /bin/bash
```

### Backend Development
```bash
# Run tests (inside backend container)
docker exec kkua-backend-1 python -m pytest tests/ -v

# Run specific test file
docker exec kkua-backend-1 python -m pytest tests/services/test_gameroom_service.py -v

# Code linting and formatting
docker exec kkua-backend-1 ruff check . --fix
docker exec kkua-backend-1 ruff format .

# Run backend in development mode (auto-reload)
docker exec kkua-backend-1 python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```bash
# Inside frontend container
docker exec kkua-frontend-1 npm start

# Build production version
docker exec kkua-frontend-1 npm run build

# Run tests
docker exec kkua-frontend-1 npm test

# Run tests in watch mode
docker exec kkua-frontend-1 npm test -- --watchAll

# Run tests with coverage
docker exec kkua-frontend-1 npm test -- --coverage --watchAll=false

# Code formatting
docker exec kkua-frontend-1 npx prettier --write src/**/*.js

# Check formatting without fixing
docker exec kkua-frontend-1 npx prettier --check src/**/*.js

# Linting
docker exec kkua-frontend-1 npx eslint --fix src/**/*.js

# Linting check only (no fix)
docker exec kkua-frontend-1 npx eslint src/**/*.js
```

### Database Operations
```bash
# Access PostgreSQL directly
docker exec -it kkua-db-1 psql -U postgres -d mydb

# Database credentials
# User: postgres
# Password: mysecretpassword
# Database: mydb
# Port: 5432
```

## Production Deployment

### Production Build
```bash
# Build and run production environment
docker-compose -f docker-compose.prod.yml up -d

# Build production frontend
docker build -f frontend/Dockerfile.prod -t kkua-frontend-prod frontend/
```

### Environment Configuration
- **Development**: Use `docker-compose.yml` with development settings
- **Production**: Use `docker-compose.prod.yml` with production optimizations
- **Environment Variables**: Copy `backend/.env.example` to `backend/.env` and configure

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
- **services/**: Business logic layer
  - `auth_service.py`: Authentication, session management, and cookie handling
  - `gameroom_service.py`: Consolidated game room management and actions logic
  - `guest_service.py`: Guest management logic
  - `session_service.py`: Thread-safe in-memory session storage with automatic cleanup
  - `game_state_service.py`: Game state management and word chain validation
  - `websocket_message_service.py`: WebSocket message processing and routing
  - `redis_game_service.py`: Redis-based real-time game state management
  - `game_data_persistence_service.py`: Critical service for persisting game results from Redis to PostgreSQL
- **schemas/**: Pydantic models for request/response validation
  - `auth_schema.py`: Authentication request/response models
  - `gameroom_schema.py`: Game room data models
  - `gameroom_actions_schema.py`: Game room action models
  - `gameroom_ws_schema.py`: WebSocket message models
  - `websocket_schema.py`: Enhanced WebSocket message validation
  - `guest_schema.py`: Guest/user data models
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
- **db/**: Database configuration and setup
  - `postgres.py`: PostgreSQL database connection and session management
- **config/**: Configuration files for cookies, logging, etc.
  - `cookie.py`: Cookie configuration settings
  - `logging_config.py`: Comprehensive logging setup with multiple log files
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
  - `GameLobbyPage/`: Individual game room lobby with chat and participant management
  - `InGame/`: Active game interface with word chain gameplay
  - `GameResult/`: Game results and statistics display page
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
- **feature/production-ready-deployment**: Current production readiness improvements

### Development Workflow
1. Create feature branch from develop: `git checkout -b feature/feature-name`
2. Make atomic commits with clear, descriptive messages
3. Test thoroughly before merging
4. Create pull request to develop for code review
5. After approval, merge to develop: `git checkout develop && git merge feature/feature-name`

### Release Workflow
1. Create release branch: `git checkout -b release/1.0.0 develop`
2. Perform final testing and bug fixes
3. Merge to main: `git checkout main && git merge --no-ff release/1.0.0`
4. Tag release: `git tag -a v1.0.0 -m "Release version 1.0.0"`
5. Merge back to develop: `git checkout develop && git merge --no-ff release/1.0.0`

### Hotfix Workflow
1. Create hotfix from main: `git checkout -b hotfix/fix-name main`
2. Fix the issue and test thoroughly
3. Merge to main: `git checkout main && git merge --no-ff hotfix/fix-name`
4. Tag if necessary: `git tag -a v1.0.1 -m "Hotfix version 1.0.1"`
5. Merge to develop: `git checkout develop && git merge --no-ff hotfix/fix-name`

### Commit Message Convention
- **feat**: New feature (e.g., `feat: Add session-based authentication`)
- **fix**: Bug fix (e.g., `fix: Resolve WebSocket connection issue`)
- **refactor**: Code refactoring (e.g., `refactor: Split ConnectionManager into focused services`)
- **test**: Adding or updating tests (e.g., `test: Add auth service unit tests`)
- **docs**: Documentation changes (e.g., `docs: Update CLAUDE.md with new architecture`)
- **chore**: Maintenance tasks (e.g., `chore: Update dependencies`)

### CI/CD Pipeline Status
- **Note**: No CI/CD configuration files found in current codebase
- **Documentation References**: `deployment-guide.md` exists but no `.github/workflows/` directory
- **Manual Deployment**: Currently using manual Docker-based deployment process

## Recent Architectural Improvements

### Phase 1: Repository Layer Optimization
- Split GameroomRepository into focused, single-responsibility components
- Removed GameroomActions class and integrated functionality
- Improved data access patterns

### Phase 2: WebSocket Architecture Refactoring
- Separated ConnectionManager into specialized managers
- Created WebSocketMessageService for message processing (528→197 lines)
- Improved separation of concerns between connection handling and business logic

### Phase 3-4: Service Layer Consolidation
- Merged GameroomActionsService into GameroomService
- Centralized WebSocket notifications
- Unified method signatures using Guest objects
- Enhanced documentation with detailed docstrings

## Development Workflow

1. **Environment Setup**: Use `docker-compose up -d` to start all services
2. **Code Changes**: Edit source files (auto-reload enabled in development)
3. **Testing**: Run backend tests with `pytest` and frontend tests with `npm test`
4. **Code Quality**: Use `ruff` for Python code formatting and `prettier`/`eslint` for JavaScript
5. **Database Changes**: Update models and run migrations if needed

## Key Configuration Files

- **docker-compose.yml**: Development environment configuration
- **docker-compose.prod.yml**: Production environment configuration
- **backend/app_config.py**: Environment-based application settings
- **backend/.env.example**: Environment variables template
- **backend/requirements.txt**: Python dependencies including pydantic-settings
- **frontend/package.json**: Node.js dependencies including React, axios, zustand
- **frontend/.prettierrc**: Frontend code formatting configuration
- **frontend/Dockerfile.prod**: Production build configuration
- **frontend/nginx.conf**: Nginx configuration for production serving
- **frontend/tailwind.config.js**: TailwindCSS configuration
- **frontend/postcss.config.js**: PostCSS configuration with TailwindCSS
- **deployment-guide.md**: Comprehensive deployment instructions

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

## Troubleshooting

### Common Docker Issues

#### Backend container fails to start
```bash
# Check logs
docker-compose logs backend

# Common solutions:
# 1. Ensure database is ready
docker-compose restart backend

# 2. Check environment variables
docker exec kkua-backend-1 env | grep DATABASE

# 3. Rebuild if dependencies changed
docker-compose build backend
```

#### Frontend hot reload not working
```bash
# Ensure CHOKIDAR_USEPOLLING is set in docker-compose.yml
# Restart the frontend container
docker-compose restart frontend
```

#### Database connection issues
```bash
# Check if database is running
docker-compose ps db

# Test database connection
docker exec -it kkua-db-1 psql -U postgres -d mydb -c "SELECT 1"

# Reset database if needed
docker-compose down -v  # Warning: This deletes all data
docker-compose up -d
```

#### Redis connection issues
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it kkua-redis-1 redis-cli ping

# Check Redis logs
docker-compose logs redis

# Clear Redis data if needed
docker exec -it kkua-redis-1 redis-cli FLUSHALL
```

### WebSocket Connection Issues

#### Connection fails immediately
- Check if backend is running: `curl http://localhost:8000/health`
- Verify WebSocket URL in frontend: Should be `ws://localhost:8000` for development
- Check browser console for CORS errors
- Ensure session cookie is present (check browser DevTools > Application > Cookies)

#### Connection drops frequently
- Check backend logs for errors: `docker-compose logs -f backend`
- Verify network stability
- Check if session is expiring
- Monitor WebSocket reconnection attempts in browser console
- Use manual reconnection button if automatic reconnection fails

### Performance Issues

#### Game performance optimization patterns
- **Timer Synchronization**: Use client-side timers with server validation to reduce WebSocket traffic
- **Selective Broadcasting**: Only broadcast timer updates at critical moments (≤10 seconds)
- **Redis Connection Pooling**: Configure max_connections=20 with keepalive for Redis client
- **Progressive Rendering**: Avoid excessive animations during gameplay for multi-window scenarios

#### WebSocket message handling best practices
- **Message Format Validation**: Always validate WebSocket message structure with Pydantic schemas
- **Error Recovery**: Implement automatic reconnection with exponential backoff (already implemented)
- **State Synchronization**: Use periodic REST API calls (3-second intervals) as WebSocket backup
- **User Feedback**: Provide visual connection status and toast notifications for connection events
- **Manual Recovery**: Offer manual reconnection controls when automatic reconnection fails

### Testing Issues

#### Tests fail with database errors
```bash
# Ensure test database is accessible
docker exec kkua-backend-1 python -m pytest tests/conftest.py -v

# Run with fresh database
docker-compose down -v
docker-compose up -d
docker-compose run --rm backend-test
```

#### Frontend tests fail
```bash
# Clear Jest cache
docker exec kkua-frontend-1 npm test -- --clearCache

# Run with no cache
docker exec kkua-frontend-1 npm test -- --no-cache
```

### Performance Issues

#### Slow API responses
- Check database query performance
- Enable backend debug logs to identify bottlenecks
- Monitor container resource usage: `docker stats`

#### High memory usage
```bash
# Check container limits
docker-compose ps

# Restart containers to free memory
docker-compose restart

# For production, set resource limits in docker-compose.prod.yml
```

## Development Tips

### Quick Development Cycle
1. Use `docker-compose logs -f [service]` to monitor specific service
2. Backend auto-reloads on file changes (uvicorn --reload)
3. Frontend hot-reloads automatically
4. Use `docker exec` for quick debugging without rebuilding

### Debugging
- Backend: Add `import pdb; pdb.set_trace()` for breakpoints
- Frontend: Use Chrome DevTools and React Developer Tools
- WebSocket: Use browser Network tab to inspect WS messages
- Database: Use `docker exec -it kkua-db-1 psql` for direct queries

### Best Practices
1. Always run tests before committing
2. Use meaningful commit messages following the convention
3. Keep Docker images updated: `docker-compose pull`
4. Clean up unused images: `docker system prune -a`
5. Use `.env` files for local configuration, never commit secrets

## Critical Development Patterns

### WebSocket Connection Management
Enhanced connection handling with user feedback:
```javascript
// Frontend - Enhanced useGameRoomSocket with toast notifications
const { 
  connected, 
  isReconnecting, 
  connectionAttempts, 
  maxReconnectAttempts,
  manualReconnect 
} = useGameRoomSocket(roomId);

// ToastContext usage for user notifications
const { showSuccess, showError, showWarning } = useToast();
```

### WebSocket Message Structure
Always follow this pattern for WebSocket message validation:
```python
# Backend - Pydantic schema validation
class GameActionMessage(BaseModel):
    type: str = "game_action"
    action: str  # toggle_ready, submit_word, etc.
    data: Dict[str, Any] = {}

# Frontend - Consistent message format
const message = {
    type: 'game_action',
    action: 'toggle_ready',
    data: {}
};
```

### Timer Implementation Best Practices
1. **Client-side Primary**: Use client-side countdown for UI responsiveness
2. **Server Validation**: Validate timing on server for security
3. **Synchronization**: Sync client timer with server at critical moments
4. **Graceful Degradation**: Fall back to server timer if client sync fails

### Authentication Flow Patterns
```javascript
// Frontend - Always include credentials for API calls
axiosInstance.defaults.withCredentials = true;

// Backend - Validate session in middleware
async def require_authentication(request: Request, db: Session = Depends(get_db)) -> Guest:
    session_token = request.cookies.get("session_token")
    # Validate and return guest object
```

### Redis vs PostgreSQL Decision Matrix
- **Use Redis for**: Active game state, real-time data, temporary data (<24h)
- **Use PostgreSQL for**: User accounts, game logs, persistent relationships
- **Hybrid approach**: Store references in PostgreSQL, active state in Redis

### Toast Notification System
Centralized user feedback with contextual messaging:
```javascript
// Setup ToastProvider in App.js (already implemented)
<ToastProvider>
  <Router>
    {/* App content */}
  </Router>
</ToastProvider>

// Usage in components
const { showSuccess, showError, showWarning, showInfo } = useToast();

// Connection events (automatically handled in useGameRoomSocket)
toast.showWarning('연결이 끊어졌습니다. 자동으로 재연결 중...', 3000);
toast.showSuccess('실시간 연결이 복구되었습니다!', 2000);
toast.showError('연결을 복구할 수 없습니다. 수동으로 재연결해주세요.', 5000);
```

### Game Result Data Handling
Robust data retrieval with retry logic:
```javascript
// Frontend - Enhanced useGameResult with retry logic
const allScoresZero = validatedPlayers.every(player => player.total_score === 0);
if (allScoresZero && retryCount < 3) {
  // Automatic retry with progressive delay
  setTimeout(() => fetchGameResult(), 2000 * (retryCount + 1));
}

// Backend - Data integrity validation
if (all_scores_zero && no_words && game_has_used_words) {
  for player in players_data:
    player.total_score = -1  # Signal incomplete processing
}
```

### Performance Optimization Guidelines
1. **Minimize WebSocket Broadcasts**: Only send critical updates
2. **Batch Database Operations**: Use bulk operations where possible
3. **Implement Client-side Caching**: Cache static data and recent API responses
4. **Progressive Enhancement**: Core functionality should work without real-time features
5. **Connection Resilience**: Use exponential backoff and user feedback for network issues
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer word chain game (끝말잇기) with item mechanics. The project uses a FastAPI backend with PostgreSQL database and a React frontend with TailwindCSS for styling.

### Recent Updates
- **Code Quality**: Complete codebase cleanup and comment optimization
  - Removed 20+ legacy files and unused components
  - Cleaned unnecessary debug comments and console.log statements
  - Standardized code documentation with focus on 'why' over 'what'
- **Bug Fixes**: Resolved critical game ending functionality
- **Authentication System**: Migrated from UUID-based to secure session-based authentication with HTTP-only cookies
- **Backend Refactoring**: Consolidated services following Single Responsibility Principle
  - Merged GameroomActions into GameroomService
  - Split ConnectionManager into focused components
  - Introduced WebSocketMessageService for message handling
- **Improved Architecture**: Enhanced separation of concerns with middleware pattern

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
- **routers/**: API endpoint definitions
  - `auth_router.py`: Authentication endpoints for session management
  - `gamerooms_router.py`: Basic CRUD operations for game rooms
  - `gameroom_actions_router.py`: Game room actions (join, leave, ready, start)
  - `gameroom_ws_router.py`: WebSocket functionality for real-time communication
  - `guests_router.py`: Guest management endpoints with session support
- **services/**: Business logic layer
  - `auth_service.py`: Authentication, session management, and cookie handling
  - `gameroom_service.py`: Consolidated game room management and actions logic
  - `guest_service.py`: Guest management logic
  - `session_service.py`: Session storage and validation with Redis-like in-memory store
  - `game_state_service.py`: Game state management and word chain validation
  - `websocket_message_service.py`: WebSocket message processing and routing
- **schemas/**: Pydantic models for request/response validation
  - `auth_schema.py`: Authentication request/response models
  - `gameroom_schema.py`: Game room data models
  - `gameroom_actions_schema.py`: Game room action models
  - `gameroom_ws_schema.py`: WebSocket message models
  - `guest_schema.py`: Guest/user data models
- **middleware/**: Custom middleware components
  - `auth_middleware.py`: Request authentication and session validation
- **websocket/**: WebSocket connection management
  - `connection_manager.py`: Game room WebSocket facade (renamed from ws_manager)
  - `websocket_manager.py`: WebSocket connection management
  - `word_chain_manager.py`: Word chain game engine
- **repositories/**: Data access layer with database operations
  - `gameroom_repository.py`: Game room and participant data access
  - `guest_repository.py`: Guest/user data access
  - `game_log_repository.py`: Game result and statistics data access
- **db/**: Database configuration and setup
- **config/**: Configuration files for cookies, logging, etc.

### Frontend Structure (React)
- **src/Pages/**: Main application pages with modular component structure
  - Each page has its own `components/` and `hooks/` subdirectories
  - `Loading/`: Initial loading/welcome page
  - `Lobby/`: Game room lobby with room list and creation
  - `GameLobbyPage/`: Individual game room lobby with chat and participant management
  - `InGame/`: Active game interface with word chain gameplay
  - `GameResult/`: Game results and statistics display page
- **src/store/**: Zustand state management
  - `guestStore.js`: Guest authentication and session management
- **src/Api/**: API communication layer
  - `axiosInstance.js`: Configured axios client with interceptors
  - `authApi.js`: Authentication API calls (login, logout, profile)
  - `roomApi.js`: Game room API calls
  - `userApi.js`: User/guest API calls
  - `wsUrl.js`: WebSocket URL configuration
- **src/utils/**: Shared utilities and components (renamed from Component)
  - `socket.js`: WebSocket connection management
  - `urls.js`: URL configuration
- **src/hooks/**: Custom React hooks
  - `useGameRoomSocket.js`: WebSocket hook for real-time game room updates

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

### CI/CD Pipeline
- **GitHub Actions**: Automated testing and deployment
- **Backend Tests**: Python tests with pytest and coverage
- **Frontend Tests**: ESLint, Prettier checks, and npm tests
- **Docker Build**: Automated production image builds
- **Auto-deploy**: Deployment on merge to main branch

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
- **.github/workflows/ci.yml**: CI/CD pipeline configuration
- **.github/workflows/pr-checks.yml**: Pull request validation
- **deployment-guide.md**: Comprehensive deployment instructions

## Environment Variables

### Backend Environment Variables
- **DATABASE_URL**: PostgreSQL connection string
  - Development: `postgresql://postgres:mysecretpassword@db:5432/mydb`
  - Production: Use your production database URL
- **HOST**: Server host (default: `0.0.0.0`)
- **PORT**: Server port (default: `8000`)
- **DEBUG**: Enable debug mode (default: `True` for dev, `False` for prod)
- **ENVIRONMENT**: Current environment (`development`, `production`, `testing`)
- **CORS_ORIGINS**: List of allowed origins for CORS
  - Development: `["http://localhost:3000", "http://127.0.0.1:3000"]`
  - Production: Add your production domain
- **TESTING**: Set to `true` when running tests

### Frontend Environment Variables
- **REACT_APP_API_URL**: Backend API URL (default: `http://localhost:8000`)
- **REACT_APP_WS_URL**: WebSocket URL (default: `ws://localhost:8000`)
- **CHOKIDAR_USEPOLLING**: Enable polling for file watching in Docker (set to `true`)

### Docker Environment
- **POSTGRES_USER**: Database user (default: `postgres`)
- **POSTGRES_PASSWORD**: Database password (default: `mysecretpassword`)
- **POSTGRES_DB**: Database name (default: `mydb`)

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
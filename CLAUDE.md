# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**끄아 (KKUA)** is a real-time multiplayer word chain game (끝말잇기) with item mechanics. The project uses a FastAPI backend with PostgreSQL database and a React frontend with TailwindCSS for styling.

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

# Code formatting
docker exec kkua-frontend-1 npx prettier --write src/**/*.js

# Linting
docker exec kkua-frontend-1 npx eslint --fix src/**/*.js

# Run tests
docker exec kkua-frontend-1 npm test
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
  - `guest_model.py`: Guest/user model with UUID-based identification
- **routers/**: API endpoint definitions
  - `gamerooms_router.py`: Basic CRUD operations for game rooms
  - `gameroom_actions_router.py`: Game room actions (join, leave, ready, start)
  - `gameroom_ws_router.py`: WebSocket functionality for real-time communication
  - `guests_router.py`: Guest management endpoints
  - `simple_ws_router.py`: Simple WebSocket testing endpoints
- **services/**: Business logic layer
  - `gameroom_service.py`: Game room management logic
  - `gameroom_actions_service.py`: Game room action handling
  - `guest_service.py`: Guest management logic
- **repositories/**: Data access layer with database operations
- **schemas/**: Pydantic models for request/response validation
- **ws_manager/**: WebSocket connection management
- **db/**: Database configuration and setup
- **config/**: Configuration files for cookies, logging, etc.

### Frontend Structure (React)
- **src/Pages/**: Main application pages with modular component structure
  - Each page has its own `components/` and `hooks/` subdirectories
  - `Loading/`: Initial loading/welcome page
  - `Lobby/`: Game room lobby with room list and creation
  - `GameLobbyPage/`: Individual game room lobby with chat and participant management
  - `InGame/`: Active game interface with word chain gameplay
- **src/store/**: Zustand state management
  - `guestStore.js`: Guest authentication and session management
- **src/Api/**: API communication layer
  - `axiosInstance.js`: Configured axios client
  - `roomApi.js`: Game room API calls
  - `userApi.js`: User/guest API calls
- **src/Component/**: Shared utilities and components
  - `socket.js`: WebSocket connection management
  - `urls.js`: URL configuration
- **src/hooks/**: Custom React hooks
  - `useGameRoomSocket.js`: WebSocket hook for real-time game room updates

### Database Schema
- **guests**: User/guest management with UUID-based identification
- **gamerooms**: Game room information with status tracking
- **gameroom_participants**: Many-to-many relationship between guests and game rooms

### Key Architectural Patterns
1. **Layered Architecture**: Controllers (routers) → Services → Repositories → Models
2. **Component-Based Frontend**: Each page is broken down into reusable components with custom hooks
3. **Real-time Communication**: WebSocket connections for live game updates and chat
4. **State Management**: Zustand for client-side state with localStorage persistence
5. **UUID-based Authentication**: Guests are identified by UUIDs for session management
6. **Environment-based Configuration**: Separate settings for development and production

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
```

## WebSocket Implementation

### Game Room WebSocket
- **URL**: `ws://localhost:8000/ws/gamerooms/{room_id}/{guest_uuid}`
- **Purpose**: Real-time game room updates, chat, and game state synchronization
- **Message Types**: Join/leave notifications, ready status updates, chat messages, game actions

### Simple WebSocket (Testing)
- **URL**: `ws://localhost:8000/simple-ws/ws`
- **Test Page**: `http://localhost:8000/static/websocket_test.html`
- **Purpose**: Basic WebSocket functionality testing

## Git Workflow

### Branch Structure
- **main**: Production-ready code
- **develop**: Development integration branch
- **feature/***: Feature development branches

### Development Workflow
1. Create feature branch from develop: `git checkout -b feature/feature-name`
2. Make changes and commit regularly
3. Test thoroughly before merging
4. Merge to develop: `git checkout develop && git merge feature/feature-name`
5. Deploy to production: `git checkout main && git merge develop`

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
1. Use `ws_manager/connection_manager.py` for backend WebSocket handling
2. Implement frontend WebSocket logic in custom hooks
3. Handle connection lifecycle (connect, disconnect, reconnect)
4. Manage message routing and state updates

## Security Considerations

- Environment-based CORS configuration
- UUID-based guest identification
- Secure WebSocket connections
- Production-ready Nginx configuration with security headers
- Environment variable management for sensitive data
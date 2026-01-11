# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BookLore is a self-hosted digital library management system for organizing, reading, and tracking PDFs, EPUBs, and comics. It consists of three main components:

- **booklore-api/** - Spring Boot 3.5 backend (Java 21)
- **booklore-ui/** - Angular 20 frontend with PrimeNG
- **ai-orchestrator/** - Python FastAPI service for AI features (MVP)

## Build Commands

### Backend (booklore-api/)
```bash
cd booklore-api
./gradlew build                    # Build the project
./gradlew test                     # Run all tests
./gradlew test --tests "com.adityachandel.booklore.SomeTest"  # Single test
./gradlew bootRun                  # Run the application
./gradlew bootRun --args='--spring.profiles.active=dev'  # Run with dev profile
```

### Frontend (booklore-ui/)
```bash
cd booklore-ui
npm install                        # Install dependencies (use --force if conflicts)
npm start                          # Development server (port 4200)
npm run build                      # Production build
npm test                           # Run Karma tests
npm run lint                       # ESLint
```

### AI Orchestrator (ai-orchestrator/)
```bash
cd ai-orchestrator
pip install -e .                   # Install dependencies
python -m app.main                 # Run the service
ruff check .                       # Linting
```

### Docker Development Stack
```bash
docker compose -f dev.docker-compose.yml up   # Full stack with hot-reload
# Frontend: http://localhost:4200
# Backend: http://localhost:8080
# Database: localhost:3366 (user: booklore, pass: booklore)
# Remote debug: localhost:5005
```

## Architecture

### Backend Structure (booklore-api/src/main/java/com/adityachandel/booklore/)
- **controller/** - REST API endpoints
- **service/** - Business logic (largest package with 23 service directories)
- **repository/** - JPA data access layer
- **model/** - Entities, DTOs, and enums
- **mapper/** - MapStruct entity-DTO mappers
- **config/** - Spring configuration classes
- **task/** - Background job processing
- **util/** - Utility classes

### Frontend Structure (booklore-ui/src/app/)
- **core/** - App-wide services, security, routing strategy
- **features/** - Feature modules: book, bookdrop, dashboard, library-creator, magic-shelf, metadata, readers, settings, stats
- **shared/** - Reusable components and utilities

### Key Technologies
- **Database**: MariaDB with Flyway migrations (auto-run on startup)
- **Auth**: JWT local auth + optional OIDC (Authentik, Pocket ID)
- **PDF/EPUB**: Apache PDFBox, epub4j-core
- **Real-time**: WebSocket with STOMP
- **Styling**: Tailwind CSS + PrimeNG components

## Development Guidelines

### Branching
- Create PRs targeting the `develop` branch (not `main`)
- Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`

### Commit Messages
Follow Conventional Commits: `feat(scope): message`, `fix(scope): message`

### Backend Development
- Create `application-dev.yml` for local overrides with custom `app.path-config` and `app.path-book` paths
- Remote debugging enabled via `REMOTE_DEBUG_ENABLED=true` env var (port 5005)
- Swagger UI available at `/api/v1/swagger-ui.html` when `SWAGGER_ENABLED=true`

### Frontend Development
- Use SCSS for component styles
- Follow Angular style guide for component/directive naming (kebab-case selectors)
- PrimeNG components with Tailwind utility classes

### Testing Requirements
- Run `./gradlew test` before creating PRs
- Backend uses JUnit 5 + AssertJ + Mockito
- Frontend uses Karma + Jasmine

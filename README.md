# Telegram Bingo Platform (Starter Scaffold)

Production-oriented starter for:
- Django + Channels backend
- PostgreSQL + Redis
- aiogram bot
- React/Vite Telegram Mini App
- Nginx reverse proxy
- Dockerized services

## Quick start

1. Copy env:
   ```bash
   cp .env.example .env
   ```
2. Build and start:
   ```bash
   docker compose up --build
   ```
3. API is available through Nginx at `http://localhost/api/...`
4. Mini App static frontend at `http://localhost/`

## Core endpoints
- `POST /api/auth/telegram-login`
- `GET /api/wallet/balance`
- `GET /api/wallet/transactions`
- `GET /api/bingo/rooms`
- `POST /api/bingo/join`

## WebSocket
- `ws://localhost/ws/rooms/10/`

## Notes
- Run migrations and seed are executed in backend entrypoint.
- `seed_initial_data` creates 1 room (10 birr) and 200 cartelas.
- Game loop Celery task exists as scaffold; schedule room loop with beat in production.

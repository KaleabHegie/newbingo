# Production Architecture

## Services
- `backend` (Django REST / Gunicorn)
- `backend_ws` (Django Channels / Daphne)
- `worker` (Celery game tasks)
- `beat` (Celery scheduler)
- `postgres` (persistent data)
- `redis` (channel layer + task broker + transient realtime state)
- `bot` (aiogram)
- `miniapp` (React/Vite static build)
- `nginx` (reverse proxy + websocket upgrade)

## Core guarantees
- Telegram-only login via initData verification.
- Room isolation for 20/30 Birr via per-room channels and tasks.
- Atomic balance updates and bet/win transaction ledger.
- Server-side bingo validation and fake-claim removal.
- DB constraints prevent duplicate cartela/user per game.

## Realtime event topology
- WS groups: `room_20_lobby`, `room_30_lobby`
- Event examples: `number_called`, `game_started`, `game_finished`, `winner_announced`, `countdown_tick`

## Security baseline
- initData hash verification.
- Short JWT access tokens.
- Server-authoritative game state.
- Audit logs for game actions.
- Row-level DB locks for critical operations.

## Horizontal scaling
- Scale `backend` and `backend_ws` replicas independently.
- Shared Redis channel layer and broker.
- PgBouncer + PostgreSQL read replica for reporting.
- Partition rooms across worker pools as room count grows.

# Development Roadmap

## Phase 1: Foundation
- Finalize Django settings and secret management.
- Implement migrations and seed strategy for rooms/cartelas.
- Establish CI lint/test pipeline.

## Phase 2: Auth + Wallet
- Complete Telegram auth flow with refresh rotation.
- Add deposit/withdraw approval lifecycle.
- Enforce idempotency keys for all money mutations.

## Phase 3: Game Engine
- Implement room orchestrator with distributed lock.
- Complete countdown/start/finish loop.
- Add strict bingo-claim debounce and anti-race handling.

## Phase 4: Realtime + Mini App UX
- Implement full WS snapshot + diff updates.
- Build cartela selection and disable state from server updates.
- Add retry/reconnect and stale-session handling.

## Phase 5: Admin + Ops
- Add admin revenue dashboards per room.
- Add user moderation and transaction review tools.
- Add observability (Prometheus/Grafana/Sentry).

## Phase 6: Hardening + Launch
- Load test to 5,000+ concurrent users.
- Security review and abuse/fraud scenarios.
- Zero-downtime deploy strategy and backup/restore drills.

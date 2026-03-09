import { useGameStore } from '../store/game.store'

const defaultWsBase =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost:8001'

const WS_BASE = (import.meta.env.VITE_WS_BASE as string) || defaultWsBase

export function connectRoomSocket(roomId: number): () => void {
  const ws = new WebSocket(`${WS_BASE}/ws/rooms/${roomId}/`)

  ws.onmessage = (ev) => {
    const payload = JSON.parse(ev.data)
    if (payload.event === 'countdown_started') {
      useGameStore.getState().onCountdownStarted(payload.starts_at, payload.seconds ?? 30)
    }
    if (payload.event === 'game_started') {
      useGameStore.getState().onGameStarted(payload.game_id)
    }
    if (payload.event === 'number_called') {
      useGameStore.getState().onNumberCalled(payload.number, payload.called_numbers ?? [])
    }
    if (payload.event === 'game_finished') {
      useGameStore.getState().onGameFinished(
        payload.winner ?? null,
        payload.prize ?? null,
        payload.winner_cartela_number ?? null,
        payload.called_numbers ?? []
      )
    }
    if (payload.event === 'player_removed') {
      useGameStore.getState().onPlayerRemoved(payload.reason ?? 'Removed from game')
    }
  }

  ws.onopen = () => {
    ws.send(JSON.stringify({ action: 'ping' }))
  }

  return () => ws.close()
}

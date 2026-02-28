import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from 'axios'

import { CartelaBoard } from '../components/CartelaBoard'
import { getCartelas, getMySeat, getRoomSummary, getRooms, joinGame } from '../services/api'
import { connectRoomSocket } from '../services/ws'
import { useAuthStore } from '../store/auth.store'
import { useGameStore } from '../store/game.store'
import type { Cartela, Room } from '../types/bingo'

export function CartelaSelectPage() {
  const navigate = useNavigate()
  const { roomId } = useParams<{ roomId: string }>()
  const currentRoomId = Number(roomId)

  const { countdownLeft, onCountdownStarted, setRoom, setGame, setSelectedCartela, tickCountdown } = useGameStore()
  const { clear } = useAuthStore()

  const [room, setRoomEntity] = useState<Room | null>(null)
  const [cartelas, setCartelas] = useState<Cartela[]>([])
  const [selected, setSelected] = useState<Cartela | null>(null)
  const [gameId, setGameIdLocal] = useState<number | null>(null)
  const [bet, setBet] = useState<number>(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!Number.isFinite(currentRoomId) || currentRoomId <= 0) return
    const close = connectRoomSocket(currentRoomId)
    return () => close()
  }, [currentRoomId])

  useEffect(() => {
    const timer = setInterval(() => tickCountdown(), 1000)
    return () => clearInterval(timer)
  }, [tickCountdown])

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const rooms = await getRooms()
        const found = rooms.find((r) => r.id === currentRoomId)
        if (!found) {
          setError('Room not found')
          setLoading(false)
          return
        }
        setBet(found.bet_amount)
        setRoomEntity(found)
        setRoom(found.bet_amount, found.id)

        const data = await getCartelas(found.id)
        setGameIdLocal(data.game_id)
        setCartelas(data.cartelas)
        const summary = await getRoomSummary(found.id)
        if (summary.countdown_left !== null) {
          const startsAt = new Date(Date.now() + summary.countdown_left * 1000).toISOString()
          onCountdownStarted(startsAt, summary.countdown_left)
        }

        const seat = await getMySeat(found.id)
        if (seat.game_id && seat.cartela_id) {
          const existingCartela = data.cartelas.find((c) => c.id === seat.cartela_id)
          if (existingCartela) {
            setSelectedCartela(existingCartela)
            setGame(seat.game_id)
            localStorage.setItem(`selected_cartela_room_${found.id}`, JSON.stringify(existingCartela))
            navigate(`/room/${found.id}/play`, { replace: true })
            return
          }
        }
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          clear()
          navigate('/')
          return
        }
        if (axios.isAxiosError(err)) {
          const detail = (err.response?.data as { detail?: string } | undefined)?.detail
          setError(detail || 'Unable to load cartelas')
        } else {
          setError('Unable to load cartelas')
        }
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [currentRoomId, setRoom, clear, navigate, onCountdownStarted, setGame, setSelectedCartela])

  const availableCount = useMemo(() => cartelas.filter((c) => !c.is_taken).length, [cartelas])
  async function continueToGame() {
    if (!room || !selected) return
    try {
      setLoading(true)
      const latest = await getCartelas(room.id)
      const latestCard = latest.cartelas.find((c) => c.id === selected.id)
      if (!latestCard || latestCard.is_taken) {
        setError('Selected cartela is already taken. Please choose another one.')
        setCartelas(latest.cartelas)
        setSelected(null)
        return
      }

      const joined = await joinGame(room.id, selected.id)
      setSelectedCartela(selected)
      setGame(joined.game_id)
      localStorage.setItem(`selected_cartela_room_${room.id}`, JSON.stringify(selected))
      navigate(`/room/${room.id}/play`)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setError(detail || 'Unable to continue to game.')
      } else {
        setError('Unable to continue to game.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-7xl bg-gradient-to-b from-cyan-100 via-white to-amber-100 p-4 text-slate-900">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Choose Cartela - {bet} Birr Room</h1>
          <p className="text-sm text-slate-700">Available: {availableCount} / {cartelas.length}</p>
          {countdownLeft !== null && <p className="text-sm font-semibold text-amber-700">Game starts in: {countdownLeft}s</p>}
        </div>
        <button onClick={() => navigate('/')} className="rounded bg-cyan-600 px-3 py-2 text-sm text-white hover:bg-cyan-700">
          Back
        </button>
      </header>

      {loading && <p className="mb-3 text-sm text-slate-700">Loading...</p>}
      {error && <p className="mb-3 text-sm text-red-400">{error}</p>}

      {selected && (
        <section className="mb-4 rounded-xl border border-cyan-200 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-lg font-semibold text-cyan-800">Selected Cartela {selected.display_number}</h2>
          <CartelaBoard cartela={selected} />
          <button
            type="button"
            onClick={continueToGame}
            disabled={loading || !gameId}
            className="mt-4 rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Continue to Called Numbers Page
          </button>
        </section>
      )}

      <section className="grid grid-cols-10 gap-1">
        {cartelas.map((c) => (
          <button
            key={c.id}
            type="button"
            disabled={c.is_taken}
            onClick={() => setSelected(c)}
            className={`rounded border px-1 py-2 text-center text-[10px] leading-tight ${
              c.is_taken
                ? 'cursor-not-allowed border-red-300 bg-red-500 text-white'
                : selected?.id === c.id
                  ? 'border-emerald-500 bg-emerald-500 text-white'
                  : 'border-slate-300 bg-slate-300 text-slate-900 hover:bg-slate-400'
            }`}
          >
            <p className="font-bold">{c.display_number}</p>
          </button>
        ))}
      </section>
    </main>
  )
}

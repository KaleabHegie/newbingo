import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from 'axios'

import { CartelaBoard } from '../components/CartelaBoard'
import { Flashboard } from '../features/flashboard/Flashboard'
import { claimBingo, getBalance, getRoomSummary, getRooms } from '../services/api'
import { connectRoomSocket } from '../services/ws'
import { useGameStore } from '../store/game.store'
import type { Cartela } from '../types/bingo'

export function PlayPage() {
  const navigate = useNavigate()
  const { roomId } = useParams<{ roomId: string }>()
  const currentRoomId = Number(roomId)
  const [bet, setBet] = useState<number>(0)
  const [balance, setBalance] = useState<string>('0.00')
  const [totalWin, setTotalWin] = useState<string>('0.00')
  const [claiming, setClaiming] = useState(false)
  const [info, setInfo] = useState<string | null>(null)

  const {
    selectedCartela,
    gameId,
    calledNumbers,
    lastNumber,
    markedNumbers,
    countdownLeft,
    gameFinished,
    winnerName,
    winnerPrize,
    removalReason,
    onCountdownStarted,
    setSelectedCartela,
    setGame,
    clearRoundMessages,
    tickCountdown,
    toggleMarkedNumber,
  } = useGameStore()

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
    getBalance()
      .then((b) => setBalance(b.balance))
      .catch(() => setBalance('0.00'))
  }, [])

  useEffect(() => {
    let active = true

    async function loadSummary() {
      try {
        const rooms = await getRooms()
        const room = rooms.find((r) => r.id === currentRoomId)
        if (!room) return
        setBet(room.bet_amount)
        const summary = await getRoomSummary(room.id)
        if (active) setTotalWin(summary.total_win)
        if (summary.game_id && active) setGame(summary.game_id)
        if (summary.countdown_left !== null && active) {
          const startsAt = new Date(Date.now() + summary.countdown_left * 1000).toISOString()
          onCountdownStarted(startsAt, summary.countdown_left)
        }
      } catch {
        if (active) setTotalWin('0.00')
      }
    }

    loadSummary()
    const timer = setInterval(loadSummary, 5000)
    return () => {
      active = false
      clearInterval(timer)
    }
  }, [currentRoomId, onCountdownStarted, setGame])

  useEffect(() => {
    if (!gameFinished && !removalReason) return
    const winnerText = winnerName ? `Winner: ${winnerName} (${winnerPrize ?? '0'} Birr)` : 'Round finished'
    setInfo(removalReason || winnerText)
    const timer = setTimeout(() => {
      clearRoundMessages()
      localStorage.removeItem(`selected_cartela_room_${currentRoomId}`)
      navigate(`/room/${currentRoomId}/cartelas`)
    }, 4000)
    return () => clearTimeout(timer)
  }, [gameFinished, removalReason, winnerName, winnerPrize, currentRoomId, navigate, clearRoundMessages])

  async function handleBingoClaim() {
    if (!gameId) {
      setInfo('Game not started yet.')
      return
    }
    try {
      setClaiming(true)
      setInfo(null)
      const result = await claimBingo(gameId)
      if (!result.valid) {
        setInfo(result.reason || 'Fake bingo. Removed from game.')
        localStorage.removeItem(`selected_cartela_room_${currentRoomId}`)
        setTimeout(() => navigate(`/room/${currentRoomId}/cartelas`), 1500)
      } else {
        setInfo(`Valid bingo. Waiting to announce winner...`)
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setInfo(detail || 'Unable to claim bingo.')
      } else {
        setInfo('Unable to claim bingo.')
      }
    } finally {
      setClaiming(false)
    }
  }

  useEffect(() => {
    if (selectedCartela) return
    const raw = localStorage.getItem(`selected_cartela_room_${currentRoomId}`)
    if (!raw) return
    try {
      const parsed = JSON.parse(raw) as Cartela
      setSelectedCartela(parsed)
    } catch {
      // ignore broken local state
    }
  }, [currentRoomId, selectedCartela, setSelectedCartela])

  const markedCount = useMemo(() => markedNumbers.length, [markedNumbers])
  const currentCallLabel = useMemo(() => {
    if (!lastNumber) return '-'
    if (lastNumber <= 15) return `B-${lastNumber}`
    if (lastNumber <= 30) return `I-${lastNumber}`
    if (lastNumber <= 45) return `N-${lastNumber}`
    if (lastNumber <= 60) return `G-${lastNumber}`
    return `O-${lastNumber}`
  }, [lastNumber])

  if (!selectedCartela) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <p className="mb-4">No cartela selected yet.</p>
        <button
          onClick={() => navigate(`/room/${currentRoomId}/cartelas`)}
          className="rounded bg-brand-500 px-4 py-2 font-semibold"
        >
          Go Select Cartela
        </button>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-7xl bg-slate-950 p-4 text-slate-100">
      <header className="mb-4 grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-amber-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-amber-300 md:text-xs">{countdownLeft !== null ? 'Starts In' : 'Current Call'}</p>
          <p className="text-xl font-black text-amber-400 md:text-3xl">
            {countdownLeft !== null ? `${countdownLeft}s` : currentCallLabel}
          </p>
        </div>
        <div className="rounded-xl border border-emerald-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-emerald-300 md:text-xs">Balance</p>
          <p className="text-xl font-black text-emerald-400 md:text-3xl">{balance} Birr</p>
        </div>
        <div className="rounded-xl border border-cyan-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-cyan-300 md:text-xs">Total Win (Deresh)</p>
          <p className="text-xl font-black text-cyan-300 md:text-3xl">{totalWin} Birr</p>
        </div>
      </header>
      {info && <p className="mb-3 rounded bg-slate-800 px-3 py-2 text-sm text-amber-300">{info}</p>}

      <section className="flex flex-row gap-4">
        <div className="rounded-xl border border-cyan-600/30 bg-slate-900 p-3" style={{ width: '60%' }}>
          <h2 className="mb-3 text-lg font-semibold text-cyan-300">Called Numbers (1-75)</h2>
          <Flashboard calledNumbers={calledNumbers} />
          <div className="mt-3 text-xs text-slate-300">
            {calledNumbers.length ? calledNumbers.join(', ') : 'No numbers called yet'}
          </div>
        </div>
        <div style={{ width: '40%' }}>
          <h2 className="mb-2 text-lg font-semibold text-indigo-300">Your Cartela</h2>
          <p className="mb-3 text-sm text-slate-300">Marked: {markedCount}</p>
          <CartelaBoard cartela={selectedCartela} markedNumbers={markedNumbers} onNumberClick={toggleMarkedNumber} />
          <button
            onClick={handleBingoClaim}
            disabled={claiming || countdownLeft !== null || !currentRoomId}
            className="mt-4 w-full rounded bg-rose-600 px-4 py-3 font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
          >
            {claiming ? 'Checking...' : 'BINGO'}
          </button>
        </div>
      </section>
    </main>
  )
}

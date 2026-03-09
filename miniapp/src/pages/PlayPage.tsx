import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from 'axios'

import { CartelaBoard } from '../components/CartelaBoard'
import { Flashboard } from '../features/flashboard/Flashboard'
import { claimBingo, getBalance, getCartelas, getRoomSummary, getRooms } from '../services/api'
import { connectRoomSocket } from '../services/ws'
import { useGameStore } from '../store/game.store'
import type { Cartela } from '../types/bingo'

function isMarked(value: number | 'FREE', called: Set<number>) {
  return value === 'FREE' || (typeof value === 'number' && called.has(value))
}

function hasWinningPattern(cartela: Cartela, calledNumbers: number[]) {
  const called = new Set(calledNumbers)
  const grid = cartela.numbers

  for (const row of grid) {
    if (row.every((value) => isMarked(value, called))) return true
  }
  for (let c = 0; c < 5; c += 1) {
    if (grid.every((row) => isMarked(row[c], called))) return true
  }
  if (grid.every((row, i) => isMarked(row[i], called))) return true
  if (grid.every((row, i) => isMarked(row[4 - i], called))) return true

  return (
    isMarked(grid[0][0], called) &&
    isMarked(grid[4][0], called) &&
    isMarked(grid[0][4], called) &&
    isMarked(grid[4][4], called)
  )
}

export function PlayPage() {
  const navigate = useNavigate()
  const { roomId } = useParams<{ roomId: string }>()
  const currentRoomId = Number(roomId)
  const [bet, setBet] = useState<number>(0)
  const [balance, setBalance] = useState<string>('0.00')
  const [totalWin, setTotalWin] = useState<string>('0.00')
  const [claiming, setClaiming] = useState(false)
  const [info, setInfo] = useState<string | null>(null)
  const [showWinnerModal, setShowWinnerModal] = useState(false)
  const [winnerCartela, setWinnerCartela] = useState<Cartela | null>(null)
  const [autoBingoEnabled, setAutoBingoEnabled] = useState(false)
  const [lastAutoClaimedGameId, setLastAutoClaimedGameId] = useState<number | null>(null)
  const lastSpokenNumberRef = useRef<number | null>(null)

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
    winnerCartelaNumber,
    finishedCalledNumbers,
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
    if (!removalReason) return
    setInfo(removalReason)
    const timer = setTimeout(() => {
      clearRoundMessages()
      localStorage.removeItem(`selected_cartela_room_${currentRoomId}`)
      navigate(`/room/${currentRoomId}/cartelas`)
    }, 4000)
    return () => clearTimeout(timer)
  }, [removalReason, currentRoomId, navigate, clearRoundMessages])

  useEffect(() => {
    if (!gameId) return
    setLastAutoClaimedGameId((prev) => (prev === gameId ? prev : null))
  }, [gameId])

  useEffect(() => {
    if (!gameFinished || removalReason) return
    setShowWinnerModal(true)
    const timer = setTimeout(() => {
      setShowWinnerModal(false)
      clearRoundMessages()
      localStorage.removeItem(`selected_cartela_room_${currentRoomId}`)
      navigate(`/room/${currentRoomId}/cartelas`)
    }, 9000)
    return () => clearTimeout(timer)
  }, [gameFinished, removalReason, currentRoomId, navigate, clearRoundMessages])

  useEffect(() => {
    let active = true

    async function loadWinnerCartela() {
      if (!showWinnerModal || !winnerCartelaNumber || !Number.isFinite(currentRoomId) || currentRoomId <= 0) {
        if (active) setWinnerCartela(null)
        return
      }
      try {
        const { cartelas } = await getCartelas(currentRoomId)
        const found = cartelas.find((c) => c.display_number === winnerCartelaNumber) ?? null
        if (active) setWinnerCartela(found)
      } catch {
        if (active) setWinnerCartela(null)
      }
    }

    loadWinnerCartela()
    return () => {
      active = false
    }
  }, [showWinnerModal, winnerCartelaNumber, currentRoomId])

  async function handleBingoClaim(isAuto = false) {
    if (!gameId) {
      setInfo('ጨዋታው ገና አልተጀመረም።')
      return
    }
    try {
      setClaiming(true)
      setInfo(isAuto ? 'AUTO BINGO በማረጋገጥ ላይ...' : null)
      const result = await claimBingo(gameId)
      if (!result.valid) {
        setInfo(result.reason || 'ሀሰተኛ ቢንጎ። ከጨዋታ ተወግደዋል።')
        localStorage.removeItem(`selected_cartela_room_${currentRoomId}`)
        setTimeout(() => navigate(`/room/${currentRoomId}/cartelas`), 1500)
      } else {
        setInfo('ትክክለኛ ቢንጎ ነው። አሸናፊ በመጠባበቅ ላይ...')
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setInfo(detail || 'ቢንጎ መጠየቅ አልተቻለም።')
      } else {
        setInfo('ቢንጎ መጠየቅ አልተቻለም።')
      }
    } finally {
      setClaiming(false)
    }
  }

  useEffect(() => {
    if (!autoBingoEnabled || !selectedCartela || !gameId || countdownLeft !== null) return
    if (claiming || gameFinished || removalReason) return
    if (lastAutoClaimedGameId === gameId) return
    if (!hasWinningPattern(selectedCartela, calledNumbers)) return

    setLastAutoClaimedGameId(gameId)
    void handleBingoClaim(true)
  }, [
    autoBingoEnabled,
    selectedCartela,
    gameId,
    countdownLeft,
    claiming,
    gameFinished,
    removalReason,
    lastAutoClaimedGameId,
    calledNumbers,
  ])

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

  useEffect(() => {
    if (countdownLeft !== null || !lastNumber) return
    if (lastSpokenNumberRef.current === lastNumber) return
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

    lastSpokenNumberRef.current = lastNumber
    const utterance = new SpeechSynthesisUtterance(currentCallLabel)
    utterance.lang = 'en-US'
    utterance.rate = 1
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
  }, [lastNumber, currentCallLabel, countdownLeft])

  if (!selectedCartela) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <p className="mb-4">እስካሁን ካርቴላ አልተመረጠም።</p>
        <button
          onClick={() => navigate(`/room/${currentRoomId}/cartelas`)}
          className="rounded bg-brand-500 px-4 py-2 font-semibold"
        >
          ካርቴላ ለመምረጥ ሂድ
        </button>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-7xl bg-slate-950 p-4 text-slate-100">
      <header className="mb-4 grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-amber-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-amber-300 md:text-xs">{countdownLeft !== null ? 'ይጀምራል በ' : 'አሁን የተጠራ'}</p>
          <p className="text-xl font-black text-amber-400 md:text-3xl">
            {countdownLeft !== null ? `${countdownLeft}s` : currentCallLabel}
          </p>
        </div>
        <div className="rounded-xl border border-emerald-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-emerald-300 md:text-xs">ቀሪ ሂሳብ</p>
          <p className="text-xl font-black text-emerald-400 md:text-3xl">{balance} ብር</p>
        </div>
        <div className="rounded-xl border border-cyan-600/30 bg-slate-900 p-3">
          <p className="text-[10px] uppercase text-cyan-300 md:text-xs">ጠቅላላ ሽልማት</p>
          <p className="text-xl font-black text-cyan-300 md:text-3xl">{totalWin} ብር</p>
        </div>
      </header>
      {info && <p className="mb-3 rounded bg-slate-800 px-3 py-2 text-sm text-amber-300">{info}</p>}
      {showWinnerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-amber-500/50 bg-slate-900 p-5 shadow-2xl">
            <h2 className="text-2xl font-black text-amber-300">የቢንጎ አሸናፊ</h2>
            <p className="mt-3 text-sm text-slate-300">
              ተጠቃሚ ስም: <span className="font-semibold text-white">{winnerName ?? 'ያልታወቀ'}</span>
            </p>
            <p className="mt-1 text-sm text-slate-300">
              የካርቴላ ቁጥር:{' '}
              <span className="font-semibold text-white">
                {winnerCartelaNumber !== null ? winnerCartelaNumber : 'ያልታወቀ'}
              </span>
            </p>
            <p className="mt-1 text-sm text-slate-300">
              ሽልማት: <span className="font-semibold text-emerald-400">{winnerPrize ?? '0'} ብር</span>
            </p>
            <p className="mt-4 text-xs uppercase tracking-wide text-cyan-300">የአሸናፊው ካርቴላ</p>
            <div className="mt-2">
              {winnerCartela ? (
                <div className="mx-auto max-w-[200px]">
                  <CartelaBoard cartela={winnerCartela} markedNumbers={finishedCalledNumbers} compact />
                </div>
              ) : (
                <div className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100">
                  የአሸናፊው ካርቴላ አልተገኘም
                </div>
              )}
            </div>
            <p className="mt-4 text-xs uppercase tracking-wide text-cyan-300">የተጠሩ ቁጥሮች</p>
            <div className="mt-2 flex max-h-32 flex-wrap gap-2 overflow-y-auto rounded-lg bg-slate-800 p-3">
              {finishedCalledNumbers.length ? (
                finishedCalledNumbers.map((n) => (
                  <span key={n} className="rounded-md bg-green-500/90 px-2 py-1 text-xs font-bold text-white">
                    {n}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-100">ቁጥሮች አልተገኙም</span>
              )}
            </div>
          </div>
        </div>
      )}

      <section className="flex flex-row gap-4">
        <div className="rounded-xl border border-cyan-600/30 bg-slate-900 p-3" style={{ width: '60%' }}>
          <h2 className="mb-3 text-lg font-semibold text-cyan-300">የተጠሩ ቁጥሮች (1-75)</h2>
          <Flashboard calledNumbers={calledNumbers} />
          <div className="mt-3 text-xs text-slate-300">
            {calledNumbers.length ? calledNumbers.join(', ') : 'እስካሁን ምንም ቁጥር አልተጠራም'}
          </div>
        </div>
        <div style={{ width: '40%' }}>
          <h2 className="mb-2 text-lg font-semibold text-indigo-300">የእርስዎ ካርቴላ</h2>
          <p className="mb-3 text-sm text-slate-300">ምልክት የተደረጉ: {markedCount}</p>
          <CartelaBoard cartela={selectedCartela} markedNumbers={markedNumbers} onNumberClick={toggleMarkedNumber} />
          <button
            type="button"
            onClick={() => setAutoBingoEnabled((prev) => !prev)}
            className={`mt-4 w-full rounded px-4 py-2 font-semibold text-white ${
              autoBingoEnabled ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-700 hover:bg-slate-600'
            }`}
          >
            {autoBingoEnabled ? 'AUTO BINGO: በርቷል' : 'AUTO BINGO: ጠፍቷል'}
          </button>
          <button
            onClick={() => handleBingoClaim(false)}
            disabled={claiming || countdownLeft !== null || !currentRoomId}
            className="mt-4 w-full rounded bg-rose-600 px-4 py-3 font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
          >
            {claiming ? 'በማረጋገጥ ላይ...' : 'ቢንጎ'}
          </button>
        </div>
      </section>
    </main>
  )
}

import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { Flashboard } from '../features/flashboard/Flashboard'
import { useGameStore } from '../store/game.store'
import { connectRoomSocket } from '../services/ws'

export function GamePage() {
  const { roomBet } = useParams<{ roomBet: string }>()
  const { calledNumbers, lastNumber } = useGameStore()

  useEffect(() => {
    if (!roomBet) return
    const close = connectRoomSocket(Number(roomBet))
    return () => close()
  }, [roomBet])

  return (
    <main className="mx-auto max-w-3xl p-4">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Room {roomBet} Birr</h1>
        <button className="rounded bg-red-600 px-4 py-2 font-semibold">BINGO</button>
      </header>
      <p className="mb-4">Last called: <span className="font-bold">{lastNumber ?? '-'}</span></p>
      <Flashboard calledNumbers={calledNumbers} />
    </main>
  )
}

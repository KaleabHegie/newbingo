import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { Flashboard } from '../features/flashboard/Flashboard'
import { useGameStore } from '../store/game.store'
import { connectRoomSocket } from '../services/ws'

export function GamePage() {
  const { roomId } = useParams<{ roomId: string }>()
  const { calledNumbers, lastNumber } = useGameStore()

  useEffect(() => {
    if (!roomId) return
    const close = connectRoomSocket(Number(roomId))
    return () => close()
  }, [roomId])

  return (
    <main className="mx-auto max-w-3xl p-4">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Room {roomId}</h1>
        <button className="rounded bg-red-600 px-4 py-2 font-semibold">BINGO</button>
      </header>
      <p className="mb-4">Last called: <span className="font-bold">{lastNumber ?? '-'}</span></p>
      <Flashboard calledNumbers={calledNumbers} />
    </main>
  )
}

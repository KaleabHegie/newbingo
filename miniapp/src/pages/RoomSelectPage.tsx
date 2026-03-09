import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

import { getRooms, loginTelegram, me, setApiToken } from '../services/api'
import { initTelegram } from '../services/telegram'
import { useAuthStore } from '../store/auth.store'
import type { Room } from '../types/bingo'

export function RoomSelectPage() {
  const navigate = useNavigate()
  const { isRegistered, setToken, clear } = useAuthStore()

  const [rooms, setRooms] = useState<Room[]>([])
  const [phoneRegistered, setPhoneRegistered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isRegistered) return
    getRooms()
      .then(async (loadedRooms) => {
        setRooms(loadedRooms)
        try {
          const profile = await me()
          setPhoneRegistered(Boolean(profile.phone_registered))
        } catch {
          setPhoneRegistered(false)
        }
      })
      .catch(async (err) => {
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          clear()
          setError('Session expired. Register again with Telegram.')
          return
        }
        setError('Unable to load rooms')
      })
  }, [isRegistered, clear])

  async function handleTelegramRegister() {
    setLoading(true)
    setError(null)
    try {
      const tg = initTelegram()
      if (!tg.initData) {
        setError('Open this app from Telegram to register with your Telegram account.')
        setLoading(false)
        return
      }
      const tokens = await loginTelegram(tg.initData)
      setToken(tokens.access)
      setApiToken(tokens.access)  
      const data = await getRooms()
      setRooms(data)
      const profile = await me()
      setPhoneRegistered(Boolean(profile.phone_registered))
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = (err.response?.data as { detail?: string } | undefined)?.detail
        setError(detail || 'Telegram registration failed. Please retry from Telegram.')
      } else {
        setError('Telegram registration failed. Please retry from Telegram.')
      }
    } finally {
      setLoading(false)
    }
  }

  const tenBirrRoom = rooms.find((r) => r.bet_amount === 10)

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-2 text-2xl font-bold">Telegram Bingo</h1>
      <p className="mb-6 text-slate-300">Play only with Telegram login.</p>
      

      {!isRegistered && (
        <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
          <p className="mb-3 text-sm text-slate-300">
            If you are not registered yet, register now with Telegram before entering the game.
          </p>
          <button
            type="button"
            disabled={loading}
            onClick={handleTelegramRegister}
            className="w-full rounded-xl bg-brand-500 px-4 py-3 font-semibold hover:bg-brand-700 disabled:opacity-60"
          >
            {loading ? 'Registering...' : 'Login with Telegram'}
          </button>
        </div>
      )}

      {isRegistered && (
        <div className="space-y-3">
          {!phoneRegistered && (
            <p className="rounded-xl border border-amber-500/50 bg-amber-900/30 px-3 py-2 text-sm text-amber-200">
              Complete phone registration in Telegram bot first: tap "Register Phone".
            </p>
          )}
          {tenBirrRoom && (
            <button
              className="w-full rounded-xl bg-brand-500 px-4 py-4 text-left font-semibold hover:bg-brand-700"
              onClick={() => navigate(`/room/${tenBirrRoom.id}/cartelas`)}
            >
              Room - 10 Birr
            </button>
          )}
          {!tenBirrRoom && <p className="text-sm text-red-400">No 10 birr room available.</p>}
        </div>
      )}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
    </main>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

import { getRooms, loginTelegram, me, setApiToken } from '../services/api'
import { initTelegram } from '../services/telegram'
import { useAuthStore } from '../store/auth.store'
import type { Room } from '../types/bingo'

export function RoomSelectPage() {
  const navigate = useNavigate()
  const { isRegistered, setToken, clear, hydrate } = useAuthStore()

  const [rooms, setRooms] = useState<Room[]>([])
  const [phoneRegistered, setPhoneRegistered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    hydrate()
  }, [hydrate])

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
          setError('ሴሽኑ አልቋል። በቴሌግራም እንደገና ይግቡ።')
          return
        }
        setError('ሩሞችን መጫን አልተቻለም።')
      })
  }, [isRegistered, clear])

  useEffect(() => {
    if (!isRegistered || !phoneRegistered || rooms.length === 0) return
    const tenBirrRoom = rooms.find((r) => r.bet_amount === 10)
    const targetRoom = tenBirrRoom ?? rooms[0]
    if (targetRoom) navigate(`/room/${targetRoom.id}/cartelas`, { replace: true })
  }, [isRegistered, phoneRegistered, rooms, navigate])

  async function handleTelegramRegister() {
    setLoading(true)
    setError(null)
    try {
      const tg = initTelegram()
      if (!tg.initData) {
        setError('እባክዎ ይህን ሚኒ አፕ ከቴሌግራም ውስጥ ይክፈቱ።')
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
        setError(detail || 'የቴሌግራም ምዝገባ አልተሳካም። እንደገና ይሞክሩ።')
      } else {
        setError('የቴሌግራም ምዝገባ አልተሳካም። እንደገና ይሞክሩ።')
      }
    } finally {
      setLoading(false)
    }
  }

  const tenBirrRoom = rooms.find((r) => r.bet_amount === 10)

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-2 text-2xl font-bold">ቴሌግራም ቢንጎ</h1>
      <p className="mb-6 text-slate-300">በቴሌግራም መግቢያ ብቻ ይጫወቱ።</p>
      

      {!isRegistered && (
        <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
          <p className="mb-3 text-sm text-slate-300">
            እስካሁን ካልተመዘገቡ ወደ ጨዋታ ከመግባትዎ በፊት በቴሌግራም ይመዝገቡ።
          </p>
          <button
            type="button"
            disabled={loading}
            onClick={handleTelegramRegister}
            className="w-full rounded-xl bg-brand-500 px-4 py-3 font-semibold hover:bg-brand-700 disabled:opacity-60"
          >
            {loading ? 'በመመዝገብ ላይ...' : 'በቴሌግራም ይግቡ'}
          </button>
        </div>
      )}

      {isRegistered && (
        <div className="space-y-3">
          {!phoneRegistered && (
            <p className="rounded-xl border border-amber-500/50 bg-amber-900/30 px-3 py-2 text-sm text-amber-200">
              በመጀመሪያ በቴሌግራም ቦት ስልክ ቁጥርዎን ያስመዝግቡ: "ስልክ ቁጥር መመዝገብ" ይጫኑ።
            </p>
          )}
          {tenBirrRoom && (
            <button
              className="w-full rounded-xl bg-brand-500 px-4 py-4 text-left font-semibold hover:bg-brand-700"
              onClick={() => navigate(`/room/${tenBirrRoom.id}/cartelas`)}
            >
              ሩም - 10 ብር
            </button>
          )}
          {!tenBirrRoom && <p className="text-sm text-red-400">10 ብር ሩም አልተገኘም።</p>}
        </div>
      )}

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
    </main>
  )
}

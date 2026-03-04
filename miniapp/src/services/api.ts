import axios from 'axios'

import type { Cartela, Room } from '../types/bingo'


const fallbackBase = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000'
const baseURL = (import.meta.env.VITE_API_BASE as string) || ""

export const api = axios.create({ baseURL })
console.log("Axios baseURL:", api.defaults.baseURL)

export function setApiToken(token: string | null) {
  if (!token) {
    delete api.defaults.headers.common.Authorization
    return
  }
  api.defaults.headers.common.Authorization = `Bearer ${token}`
}

export async function loginTelegram(initData: string): Promise<{ access: string; refresh: string }> {
  const { data } = await api.post(`/api/auth/telegram-login`, { init_data: initData })
  return data
}

export async function me(): Promise<{ phone_registered: boolean; phone_number: string | null }> {
  const { data } = await api.get('/api/auth/me')
  return data
}

export async function getRooms(): Promise<Room[]> {
  const { data } = await api.get('/api/bingo/rooms')
  return data
}

export async function getCartelas(roomId: number): Promise<{ game_id: number; cartelas: Cartela[] }> {
  const { data } = await api.get('/api/bingo/cartelas', { params: { room_id: roomId } })
  return data
}

export async function getMySeat(roomId: number): Promise<{ game_id: number | null; cartela_id: number | null }> {
  const { data } = await api.get('/api/bingo/my-seat', { params: { room_id: roomId } })
  return data
}

export async function getRoomSummary(
  roomId: number
): Promise<{
  game_id: number | null
  status: 'waiting' | 'running' | 'finished'
  total_players: number
  total_win: string
  countdown_left: number | null
  winner: string | null
}> {
  const { data } = await api.get('/api/bingo/summary', { params: { room_id: roomId } })
  return data
}

export async function joinGame(roomId: number, cartelaId: number): Promise<{ game_id: number; cartela_id: number }> {
  const { data } = await api.post('/api/bingo/join', { room_id: roomId, cartela_id: cartelaId })
  return data
}

export async function getBalance(): Promise<{ balance: string }> {
  const { data } = await api.get('/api/wallet/balance')
  return data
}

export async function claimBingo(gameId: number): Promise<{ valid: boolean; prize?: string; reason?: string }> {
  const { data } = await api.post('/api/bingo/claim', { game_id: gameId })
  return data
}

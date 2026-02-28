import { create } from 'zustand'

import { setApiToken } from '../services/api'

type AuthState = {
  token: string | null
  isRegistered: boolean
  setToken: (token: string) => void
  clear: () => void
}

const persisted = localStorage.getItem('bingo_access_token')
if (persisted) {
  setApiToken(persisted)
}

export const useAuthStore = create<AuthState>((set) => ({
  token: persisted,
  isRegistered: !!persisted,
  setToken: (token) => {
    localStorage.setItem('bingo_access_token', token)
    setApiToken(token)
    set({ token, isRegistered: true })
  },
  clear: () => {
    localStorage.removeItem('bingo_access_token')
    set({ token: null, isRegistered: false })
  },
}))

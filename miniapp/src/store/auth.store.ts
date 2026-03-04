import { create } from 'zustand'
import { setApiToken } from '../services/api'

type AuthState = {
  token: string | null
  isRegistered: boolean
  hydrate: () => void
  setToken: (token: string) => void
  clear: () => void
}

const STORAGE_KEY = 'bingo_access_token'

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  isRegistered: false,

  hydrate: () => {
    if (typeof window === 'undefined') return
    const persisted = window.localStorage.getItem(STORAGE_KEY)
    if (persisted) {
      setApiToken(persisted)
      set({ token: persisted, isRegistered: true })
    }
  },

  setToken: (token) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, token)
    }
    setApiToken(token)
    set({ token, isRegistered: true })
  },

  clear: () => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY)
    }
    // also remove auth header
    setApiToken('') // <-- change setApiToken to delete header when empty (see below)
    set({ token: null, isRegistered: false })
  },
}))
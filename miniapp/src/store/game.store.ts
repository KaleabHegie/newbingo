import { create } from 'zustand'

import type { Cartela } from '../types/bingo'

type GameState = {
  roomBet: number | null
  roomId: number | null
  gameId: number | null
  selectedCartela: Cartela | null
  calledNumbers: number[]
  lastNumber: number | null
  markedNumbers: number[]
  countdownEndsAt: string | null
  countdownLeft: number | null
  gameFinished: boolean
  winnerName: string | null
  winnerPrize: string | null
  winnerCartelaNumber: number | null
  finishedCalledNumbers: number[]
  removalReason: string | null
  setRoom: (bet: number, roomId: number) => void
  setGame: (gameId: number) => void
  setSelectedCartela: (cartela: Cartela) => void
  onNumberCalled: (n: number, called: number[]) => void
  onCountdownStarted: (startsAt: string, seconds: number) => void
  onGameStarted: (gameId: number) => void
  onGameFinished: (
    winner: string | null,
    prize: string | null,
    winnerCartelaNumber: number | null,
    calledNumbers: number[]
  ) => void
  onPlayerRemoved: (reason: string) => void
  clearRoundMessages: () => void
  tickCountdown: () => void
  toggleMarkedNumber: (n: number) => void
}

export const useGameStore = create<GameState>((set, get) => ({
  roomBet: null,
  roomId: null,
  gameId: null,
  selectedCartela: null,
  calledNumbers: [],
  lastNumber: null,
  markedNumbers: [],
  countdownEndsAt: null,
  countdownLeft: null,
  gameFinished: false,
  winnerName: null,
  winnerPrize: null,
  winnerCartelaNumber: null,
  finishedCalledNumbers: [],
  removalReason: null,
  setRoom: (bet, roomId) =>
    set({
      roomBet: bet,
      roomId,
      calledNumbers: [],
      lastNumber: null,
      markedNumbers: [],
      countdownEndsAt: null,
      countdownLeft: null,
      gameFinished: false,
      winnerName: null,
      winnerPrize: null,
      winnerCartelaNumber: null,
      finishedCalledNumbers: [],
      removalReason: null,
      gameId: null,
    }),
  setGame: (gameId) => set({ gameId }),
  setSelectedCartela: (cartela) => set({ selectedCartela: cartela, markedNumbers: [] }),
  onNumberCalled: (n, called) =>
    set({
      lastNumber: n,
      calledNumbers: called,
      countdownEndsAt: null,
      countdownLeft: null,
      gameFinished: false,
      winnerName: null,
      winnerPrize: null,
      winnerCartelaNumber: null,
      finishedCalledNumbers: [],
      removalReason: null,
    }),
  onCountdownStarted: (startsAt, seconds) => set({ countdownEndsAt: startsAt, countdownLeft: seconds }),
  onGameStarted: (gameId) =>
    set({
      gameId,
      gameFinished: false,
      winnerName: null,
      winnerPrize: null,
      winnerCartelaNumber: null,
      finishedCalledNumbers: [],
      removalReason: null,
      countdownEndsAt: null,
      countdownLeft: null,
      calledNumbers: [],
      lastNumber: null,
      markedNumbers: [],
    }),
  onGameFinished: (winner, prize, winnerCartelaNumber, calledNumbers) =>
    set({
      gameFinished: true,
      winnerName: winner,
      winnerPrize: prize,
      winnerCartelaNumber,
      finishedCalledNumbers: calledNumbers,
    }),
  onPlayerRemoved: (reason) => set({ removalReason: reason }),
  clearRoundMessages: () =>
    set({
      gameFinished: false,
      winnerName: null,
      winnerPrize: null,
      winnerCartelaNumber: null,
      finishedCalledNumbers: [],
      removalReason: null,
    }),
  tickCountdown: () => {
    const state = get()
    if (!state.countdownEndsAt) return
    const ends = new Date(state.countdownEndsAt).getTime()
    const left = Math.max(0, Math.ceil((ends - Date.now()) / 1000))
    set({ countdownLeft: left, countdownEndsAt: left === 0 ? null : state.countdownEndsAt })
  },
  toggleMarkedNumber: (n) => {
    const state = get()

    const exists = state.markedNumbers.includes(n)
    set({
      markedNumbers: exists ? state.markedNumbers.filter((x) => x !== n) : [...state.markedNumbers, n],
    })
  },
}))

export type Room = {
  id: number
  bet_amount: number
  total_cartelas: number
  is_active: boolean
}

export type Cartela = {
  id: number
  room_id: number
  numbers: Array<Array<number | 'FREE'>>
  predefined: boolean
  is_taken: boolean
}

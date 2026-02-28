import { Navigate, Route, Routes } from 'react-router-dom'

import { CartelaSelectPage } from '../pages/CartelaSelectPage'
import { PlayPage } from '../pages/PlayPage'
import { RoomSelectPage } from '../pages/RoomSelectPage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<RoomSelectPage />} />
      <Route path="/room/:roomId/cartelas" element={<CartelaSelectPage />} />
      <Route path="/room/:roomId/play" element={<PlayPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

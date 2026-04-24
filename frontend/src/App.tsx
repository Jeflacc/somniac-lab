import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LabPage from './pages/LabPage'

export default function App() {
  return (
    <Routes>
      <Route path="/"     element={<LandingPage />} />
      <Route path="/lab/*" element={<LabPage />} />
    </Routes>
  )
}

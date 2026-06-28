import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Measurements from './pages/Measurements'
import GarminSync from './pages/GarminSync'
import ProfilePage from './pages/Profile'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"             element={<Dashboard />} />
          <Route path="/measurements" element={<Measurements />} />
          <Route path="/garmin"       element={<GarminSync />} />
          <Route path="/profile"      element={<ProfilePage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

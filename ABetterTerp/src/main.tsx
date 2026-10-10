import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import App from './App.tsx'
import Register from './pages/Register.tsx'
import Login from './pages/LoginPage.tsx'
import Home from './pages/home.tsx'
import Workouts from './pages/Workouts.tsx'
import WaterIntake from './pages/WaterIntake.tsx'
import Assignments from './pages/Assignments.tsx'
import Exams from './pages/Exams.tsx'

// Attach the JWT to every request to the API, and return to login when it is rejected.
const API_ORIGIN = 'http://localhost:8000'
const originalFetch = window.fetch.bind(window)
window.fetch = async (input, init) => {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
  if (!url.startsWith(API_ORIGIN)) return originalFetch(input, init)

  const token = localStorage.getItem('token')
  const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined))
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await originalFetch(input, { ...init, headers })
  const isAuthRoute = url.endsWith('/login') || url.endsWith('/register')
  if (res.status === 401 && !isAuthRoute) {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.assign('/login')
  }
  return res
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Register />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/home" element={<Home />} />
      <Route path="/workouts" element={<Workouts />} />
      <Route path="/water" element={<WaterIntake />} />
      <Route path="/assignments" element={<Assignments />} />
      <Route path="/exams" element={<Exams />} />
    </Routes>
  </BrowserRouter>
)
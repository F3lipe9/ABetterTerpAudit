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
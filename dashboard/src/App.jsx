import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import EvaluatePage from './pages/Evaluate'
import ClaimsPage from './pages/Claims'
import RAGPage from './pages/RAG'
import AgentPage from './pages/Agent'
import ComparePage from './pages/Compare'
import BenchmarkPage from './pages/Benchmark'
import LeaderboardPage from './pages/Leaderboard'
import ProxyPage from './pages/Proxy'
import PaperPage from './pages/Paper'
import HistoryPage from './pages/History'

export default function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          <Route path="/"            element={<EvaluatePage />} />
          <Route path="/claims"      element={<ClaimsPage />} />
          <Route path="/rag"         element={<RAGPage />} />
          <Route path="/agent"       element={<AgentPage />} />
          <Route path="/compare"     element={<ComparePage />} />
          <Route path="/benchmark"   element={<BenchmarkPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/proxy"       element={<ProxyPage />} />
          <Route path="/paper"       element={<PaperPage />} />
          <Route path="/history"     element={<HistoryPage />} />
        </Routes>
      </main>
    </div>
  )
}

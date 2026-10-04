import { useEffect, useState } from 'react'

export default function App() {
  const [health, setHealth] = useState<string>('checking...')
  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(d => setHealth(JSON.stringify(d)))
      .catch(e => setHealth('api unreachable: ' + e))
  }, [])
  return (
    <main style={{ fontFamily: 'system-ui', padding: 32, maxWidth: 820 }}>
      <h1 style={{ color: '#1E2761' }}>ADTM</h1>
      <p>Sovereign ERP migration accelerator — Oracle EBS → Fusion. Phase-0 skeleton.</p>
      <p><strong>API health:</strong> {health}</p>
      <p style={{ color: '#555' }}>Phase 1 screens: connections, schema discovery, extraction,
      DQ, mapping, simulation, load, reconciliation, audit.</p>
    </main>
  )
}

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './interactive-features.js'
import InteractiveModernApp from './InteractiveModernApp.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <InteractiveModernApp />
  </StrictMode>,
)

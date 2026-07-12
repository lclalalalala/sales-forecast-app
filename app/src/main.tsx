import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { ThemeProvider } from 'next-themes'
import { AnalysisProvider } from '@/state/analysisContext'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      themes={['light', 'dark']}
      value={{ light: 'theme-light', dark: 'theme-dark' }}
      storageKey="sephora-theme"
      enableColorScheme={false}
    >
      <BrowserRouter>
        <AnalysisProvider>
          <App />
        </AnalysisProvider>
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
)

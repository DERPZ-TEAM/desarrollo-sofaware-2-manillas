// Punto de entrada: monta React dentro de <div id="root"> (index.html).
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import AvisoServidor from './components/AvisoServidor'
import { AuthProvider } from './context/AuthContext'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
        <AvisoServidor />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)

/**
 * "Guardias" de rutas en el frontend.
 *
 * OJO: esto solo mejora la experiencia (redirige a la pantalla correcta).
 * La SEGURIDAD real está en el backend: aunque alguien manipule el navegador,
 * la API rechaza con 401/403 a quien no tenga el rol adecuado.
 */
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RequireCustomer({ children }) {
  const { user, isAdmin } = useAuth()
  const location = useLocation()
  if (!user) return <Navigate to="/ingresar" replace state={{ from: location.pathname }} />
  if (isAdmin) return <Navigate to="/admin" replace />
  return children
}

export function RequireAdmin({ children }) {
  const { user, isAdmin } = useAuth()
  if (!user) return <Navigate to="/admin/ingresar" replace />
  if (!isAdmin) return <Navigate to="/" replace />
  return children
}

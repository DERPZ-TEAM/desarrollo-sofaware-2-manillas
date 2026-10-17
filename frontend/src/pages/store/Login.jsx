import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/AuthShell'
import { Alert, Field } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'

/** Inicio de sesión de CLIENTES (HU-AU-002). Acepta usuario o correo. */
export default function Login() {
  const { login, user, isAdmin, aviso } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to={isAdmin ? '/admin' : '/'} replace />

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.username.trim() || !form.password) {
      setError('Escribe tu usuario (o correo) y tu contraseña.')
      return
    }
    setLoading(true)
    try {
      await login(form.username.trim(), form.password)
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      setError(err.data?.admin ? 'Esta es una cuenta de administrador. Ingresa por el panel de gestión.' : err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Iniciar sesión"
      subtitle="Accede para comprar y seguir tus pedidos."
      side={{ title: 'Bienvenida de nuevo', text: 'Tus piezas favoritas te esperan.' }}
    >
      <form onSubmit={onSubmit} noValidate>
        <Alert type="info">{aviso}</Alert>
        <Alert>{error}</Alert>
        <Field label="Usuario o correo">
          <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="username" autoFocus />
        </Field>
        <Field label="Contraseña">
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="current-password" />
        </Field>
        <div className="form-links"><Link to="/recuperar">¿Olvidaste tu contraseña?</Link></div>
        <button className="btn btn-dark btn-block" disabled={loading}>{loading ? 'Entrando…' : 'Iniciar sesión'}</button>
      </form>
      <p className="muted center">¿No tienes cuenta? <Link to="/registro">Regístrate</Link></p>
      <p className="muted center small"><Link to="/admin/ingresar">Acceso administrador</Link></p>
    </AuthShell>
  )
}

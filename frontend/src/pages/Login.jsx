import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const { login, user, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user && isAdmin) return <Navigate to="/admin" replace />
  if (user) return <Navigate to="/" replace />

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.username.trim() || !form.password) {
      setError('Escribe tu usuario y contraseña.')
      return
    }
    setLoading(true)
    try {
      const u = await login(form.username, form.password, false)
      if (u.is_staff) navigate('/admin')
      else navigate('/')
    } catch (err) {
      if (err.payload?.admin) {
        setError('Esta es una cuenta de administrador. Entra por el panel de gestión.')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <Link to="/" className="brand" style={{ color: 'white' }}>GOLDBRACELETS</Link>
        <h1 className="serif" style={{ fontSize: 56, marginBottom: 0 }}>Bienvenida de nuevo</h1>
        <p>Entra para guardar tus piezas favoritas y completar tu pedido.</p>
      </div>
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <h1>Iniciar sesión</h1>
        <p className="hint">Clientes de GoldBracelets</p>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>Usuario</label>
          <input value={form.username} onChange={(e) => set('username', e.target.value)} autoComplete="username" />
        </div>
        <div className="field">
          <label>Contraseña</label>
          <input type="password" value={form.password} onChange={(e) => set('password', e.target.value)} autoComplete="current-password" />
        </div>
        <button className="btn btn-dark" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
        <p className="hint">¿Aún no tienes cuenta? <Link to="/registro">Regístrate</Link></p>
        <p className="hint"><Link to="/admin/ingresar">Soy administrador</Link></p>
      </form>
    </div>
  )
}

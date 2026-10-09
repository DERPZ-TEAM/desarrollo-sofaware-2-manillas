import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../AuthContext'

export default function AdminLogin() {
  const { login, isAdmin, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAdmin) return <Navigate to="/admin" replace />
  if (user) return <Navigate to="/" replace />

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.username || !form.password) {
      setError('Usuario y contraseña de administrador son obligatorios.')
      return
    }
    setLoading(true)
    try {
      await login(form.username, form.password, true)
      navigate('/admin')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page" style={{ gridTemplateColumns: '240px 1fr', minHeight: '100vh' }}>
      <aside className="sidebar">
        <h2>GOLDBRACELETS</h2>
        <p style={{ padding: '0 22px', fontSize: 13, color: '#9aa5ad' }}>Gestión de la joyería</p>
      </aside>
      <form className="auth-form" onSubmit={onSubmit} style={{ maxWidth: 480 }}>
        <p className="hint">Escritorio · Administrador</p>
        <h1>Ingresar al panel</h1>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>Usuario administrador</label>
          <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        </div>
        <div className="field">
          <label>Contraseña</label>
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        <button className="btn btn-dark" disabled={loading}>{loading ? 'Verificando...' : 'Entrar'}</button>
        <p className="hint"><Link to="/ingresar">Soy cliente</Link></p>
      </form>
    </div>
  )
}

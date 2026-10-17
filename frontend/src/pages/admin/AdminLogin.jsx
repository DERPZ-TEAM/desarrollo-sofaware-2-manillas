import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/AuthShell'
import { Alert, Field } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'

/** Login EXCLUSIVO del administrador: usa /api/auth/admin/login/. */
export default function AdminLogin() {
  const { login, isAdmin, user, aviso } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAdmin) return <Navigate to="/admin" replace />
  if (user) return <Navigate to="/" replace />

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!form.username.trim() || !form.password) {
      setError('Usuario y contraseña de administrador son obligatorios.')
      return
    }
    setLoading(true)
    try {
      await login(form.username.trim(), form.password, true)
      navigate('/admin', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell admin title="Panel de gestión" subtitle="Acceso restringido al administrador de la tienda."
      side={{ title: 'Administración', text: 'Gestiona productos, inventario, pedidos y reportes.' }}>
      <form onSubmit={onSubmit} noValidate>
        <Alert type="info">{aviso}</Alert>
        <Alert>{error}</Alert>
        <Field label="Usuario administrador">
          <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} autoComplete="username" autoFocus />
        </Field>
        <Field label="Contraseña">
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="current-password" />
        </Field>
        <button className="btn btn-gold btn-block" disabled={loading}>{loading ? 'Verificando…' : 'Entrar al panel'}</button>
      </form>
      <p className="muted center"><Link to="/ingresar">Soy cliente</Link> · <Link to="/">Ir a la tienda</Link></p>
    </AuthShell>
  )
}

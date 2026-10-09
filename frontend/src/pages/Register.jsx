import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const empty = {
  username: '', email: '', primer_nombre: '', apellidos: '',
  telefono: '', password: '', password2: '',
}

export default function Register() {
  const { register, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/" replace />

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  function validate() {
    if (form.username.trim().length < 4) return 'El usuario debe tener al menos 4 caracteres.'
    if (!/^[a-zA-Z0-9._]+$/.test(form.username.trim())) return 'El usuario solo admite letras, números, punto o guion bajo.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return 'Escribe un correo válido.'
    if (form.primer_nombre.trim().length < 2) return 'Escribe tu nombre.'
    if (form.apellidos.trim().length < 2) return 'Escribe tus apellidos.'
    if (form.password.length < 8) return 'La contraseña debe tener mínimo 8 caracteres.'
    if (!/[A-Za-z]/.test(form.password) || !/[0-9]/.test(form.password)) return 'La contraseña debe mezclar letras y números.'
    if (form.password !== form.password2) return 'Las contraseñas no coinciden.'
    return ''
  }

  async function onSubmit(e) {
    e.preventDefault()
    const v = validate()
    if (v) { setError(v); return }
    setLoading(true)
    setError('')
    try {
      await register(form)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <Link to="/" className="brand" style={{ color: 'white' }}>GOLDBRACELETS</Link>
        <h1 className="serif" style={{ fontSize: 52 }}>Únete a la casa</h1>
        <p>Crea tu cuenta de cliente para comprar pulseras y piezas GoldBracelets.</p>
      </div>
      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <h1>Crear cuenta</h1>
        {error && <div className="error">{error}</div>}
        <div className="two">
          <div className="field"><label>Nombre</label><input value={form.primer_nombre} onChange={(e) => set('primer_nombre', e.target.value)} /></div>
          <div className="field"><label>Apellidos</label><input value={form.apellidos} onChange={(e) => set('apellidos', e.target.value)} /></div>
        </div>
        <div className="field"><label>Usuario</label><input value={form.username} onChange={(e) => set('username', e.target.value)} /></div>
        <div className="field"><label>Correo</label><input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} /></div>
        <div className="field"><label>Teléfono</label><input value={form.telefono} onChange={(e) => set('telefono', e.target.value)} /></div>
        <div className="two">
          <div className="field"><label>Contraseña</label><input type="password" value={form.password} onChange={(e) => set('password', e.target.value)} /></div>
          <div className="field"><label>Confirmar</label><input type="password" value={form.password2} onChange={(e) => set('password2', e.target.value)} /></div>
        </div>
        <button className="btn btn-dark" disabled={loading}>{loading ? 'Creando...' : 'Registrarme'}</button>
        <p className="hint">¿Ya tienes cuenta? <Link to="/ingresar">Inicia sesión</Link></p>
      </form>
    </div>
  )
}

import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import AuthShell from '../../components/AuthShell'
import { Alert, Field } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import PasswordInput from '../../components/PasswordInput'
import { TIPOS_DOCUMENTO, errorDocumento } from '../../utils/format'

const VACIO = {
  primer_nombre: '', apellidos: '', tipo_documento: 'CC', numero_documento: '',
  username: '', email: '', telefono: '', password: '', password2: '',
}

/**
 * Registro de clientes (HU-US-001, HU-SE-033).
 * Valida en el navegador (respuesta inmediata) y el backend vuelve a validar (seguridad).
 */
export default function Register() {
  const { register, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(VACIO)
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/" replace />

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })) }

  function validar() {
    const e = {}
    if (form.primer_nombre.trim().length < 2) e.primer_nombre = 'Escribe tu nombre.'
    if (form.apellidos.trim().length < 2) e.apellidos = 'Escribe tus apellidos.'
    const doc = errorDocumento(form.tipo_documento, form.numero_documento)
    if (doc) e.numero_documento = doc
    if (form.username.trim().length < 4) e.username = 'Mínimo 4 caracteres.'
    else if (!/^[a-zA-Z0-9._]+$/.test(form.username.trim())) e.username = 'Solo letras, números, punto o guion bajo.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) e.email = 'Escribe un correo válido.'
    if (form.telefono && !/^[0-9+\-\s()]{7,20}$/.test(form.telefono)) e.telefono = 'Teléfono no válido.'
    if (form.password.length < 8) e.password = 'Mínimo 8 caracteres.'
    else if (!/[A-Za-z]/.test(form.password) || !/[0-9]/.test(form.password)) e.password = 'Mezcla letras y números.'
    if (form.password !== form.password2) e.password2 = 'Las contraseñas no coinciden.'
    return e
  }

  async function onSubmit(ev) {
    ev.preventDefault()
    const e = validar()
    setErrors(e)
    if (Object.keys(e).length) { setError('Revisa los campos marcados en rojo.'); return }
    setLoading(true)
    setError('')
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      setErrors(err.fields)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Crear cuenta"
      subtitle="Regístrate como cliente de GoldBracelets."
      side={{ title: 'Únete a la casa', text: 'Compra pulseras y joyería en oro con envío a toda Colombia.' }}
    >
      <form onSubmit={onSubmit} noValidate>
        <Alert>{error}</Alert>
        <div className="two">
          <Field label="Nombre" error={errors.primer_nombre}><input value={form.primer_nombre} onChange={(e) => set('primer_nombre', e.target.value)} /></Field>
          <Field label="Apellidos" error={errors.apellidos}><input value={form.apellidos} onChange={(e) => set('apellidos', e.target.value)} /></Field>
        </div>
        <div className="two">
          <Field label="Tipo de documento">
            <select value={form.tipo_documento} onChange={(e) => set('tipo_documento', e.target.value)}>
              {TIPOS_DOCUMENTO.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </Field>
          <Field label="Número de documento" error={errors.numero_documento}>
            <input value={form.numero_documento} onChange={(e) => set('numero_documento', e.target.value)} inputMode={['CC', 'TI'].includes(form.tipo_documento) ? 'numeric' : 'text'} />
          </Field>
        </div>
        <div className="two">
          <Field label="Usuario" error={errors.username}><input value={form.username} onChange={(e) => set('username', e.target.value)} autoComplete="username" /></Field>
          <Field label="Teléfono (opcional)" error={errors.telefono}><input value={form.telefono} onChange={(e) => set('telefono', e.target.value)} inputMode="tel" /></Field>
        </div>
        <Field label="Correo" error={errors.email}><input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} autoComplete="email" /></Field>
        <div className="two">
          <Field label="Contraseña" error={errors.password}><PasswordInput value={form.password} onChange={(e) => set('password', e.target.value)} autoComplete="new-password" /></Field>
          <Field label="Confirmar" error={errors.password2}><PasswordInput value={form.password2} onChange={(e) => set('password2', e.target.value)} autoComplete="new-password" /></Field>
        </div>
        <button className="btn btn-dark btn-block" disabled={loading}>{loading ? 'Creando cuenta…' : 'Registrarme'}</button>
      </form>
      <p className="muted center">¿Ya tienes cuenta? <Link to="/ingresar">Inicia sesión</Link></p>
    </AuthShell>
  )
}

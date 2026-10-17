import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import AuthShell from '../../components/AuthShell'
import { Alert, Field } from '../../components/ui'

/** Recuperar contraseña, paso 1: pedir el enlace al correo (HU-US-003). */
export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [enlace, setEnlace] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setEnlace('')
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setMsg({ type: 'error', text: 'Escribe un correo válido.' })
      return
    }
    setLoading(true)
    try {
      const data = await api('/auth/password/recuperar/', { method: 'POST', body: { email: email.trim() }, auth: false })
      setMsg({ type: 'ok', text: data.detail })
      if (data.enlace_demo) setEnlace(data.enlace_demo.replace(/^https?:\/\/[^/]+/, ''))
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Recuperar contraseña" subtitle="Te enviaremos un enlace para crear una nueva."
      side={{ title: 'Tranquila(o)', text: 'Recupera el acceso a tu cuenta en un minuto.' }}>
      <form onSubmit={onSubmit} noValidate>
        <Alert type={msg.type}>{msg.text}</Alert>
        {enlace && (
          <Alert type="info">Modo demostración (sin servidor de correo): <Link to={enlace}>abrir enlace de recuperación</Link></Alert>
        )}
        <Field label="Correo registrado"><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus /></Field>
        <button className="btn btn-dark btn-block" disabled={loading}>{loading ? 'Enviando…' : 'Recuperar'}</button>
      </form>
      <p className="muted center"><Link to="/ingresar">Volver a iniciar sesión</Link></p>
    </AuthShell>
  )
}

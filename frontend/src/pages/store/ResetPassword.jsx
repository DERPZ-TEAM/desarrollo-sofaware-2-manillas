import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import AuthShell from '../../components/AuthShell'
import { Alert, Field } from '../../components/ui'

/** Recuperar contraseña, paso 2: el enlace del correo trae uid y token. */
export default function ResetPassword() {
  const { uid, token } = useParams()
  const [form, setForm] = useState({ password: '', password2: '' })
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [listo, setListo] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    if (form.password.length < 8) return setMsg({ type: 'error', text: 'La contraseña debe tener mínimo 8 caracteres.' })
    if (form.password !== form.password2) return setMsg({ type: 'error', text: 'Las contraseñas no coinciden.' })
    try {
      const data = await api('/auth/password/restablecer/', { method: 'POST', auth: false, body: { uid, token, ...form } })
      setMsg({ type: 'ok', text: data.detail })
      setListo(true)
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    }
    return undefined
  }

  return (
    <AuthShell title="Nueva contraseña" side={{ title: 'Casi listo', text: 'Elige una contraseña segura.' }}>
      <Alert type={msg.type}>{msg.text}</Alert>
      {listo ? (
        <Link to="/ingresar" className="btn btn-dark btn-block">Iniciar sesión</Link>
      ) : (
        <form onSubmit={onSubmit} noValidate>
          <Field label="Nueva contraseña" hint="Mínimo 8 caracteres, letras y números.">
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" />
          </Field>
          <Field label="Confirmar contraseña">
            <input type="password" value={form.password2} onChange={(e) => setForm({ ...form, password2: e.target.value })} autoComplete="new-password" />
          </Field>
          <button className="btn btn-dark btn-block">Guardar contraseña</button>
        </form>
      )}
    </AuthShell>
  )
}

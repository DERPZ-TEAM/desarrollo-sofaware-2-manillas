import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader, StatusBadge } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { fecha, money } from '../../utils/format'

/** Mi cuenta: datos personales (HU-US-004), contraseña e historial de pedidos (HU-PE-023). */
export default function Profile() {
  const { user, updateUser } = useAuth()
  const [tab, setTab] = useState('pedidos')
  const [pedidos, setPedidos] = useState(null)
  const [form, setForm] = useState({
    first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '',
    telefono: user.telefono || '', direccion: user.direccion || '', ciudad: user.ciudad || '', departamento: user.departamento || '',
  })
  const [pass, setPass] = useState({ password_actual: '', password: '', password2: '' })
  const [errors, setErrors] = useState({})
  const [msg, setMsg] = useState({ type: '', text: '' })

  useEffect(() => { api('/pedidos/').then(setPedidos).catch(() => setPedidos([])) }, [])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  async function guardar(e) {
    e.preventDefault()
    setErrors({})
    if (!form.first_name.trim() || !form.last_name.trim() || !form.email.trim()) {
      setMsg({ type: 'error', text: 'Nombre, apellidos y correo son obligatorios.' })
      return
    }
    try {
      const data = await api('/auth/me/', { method: 'PUT', body: form })
      updateUser(data)
      setMsg({ type: 'ok', text: 'Información actualizada correctamente.' })
    } catch (err) {
      setErrors(err.fields)
      setMsg({ type: 'error', text: err.message })
    }
  }

  async function cambiarClave(e) {
    e.preventDefault()
    setErrors({})
    try {
      const data = await api('/auth/password/cambiar/', { method: 'POST', body: pass })
      setPass({ password_actual: '', password: '', password2: '' })
      setMsg({ type: 'ok', text: data.detail })
    } catch (err) {
      setErrors(err.fields)
      setMsg({ type: 'error', text: err.message })
    }
  }

  return (
    <div className="wrap section">
      <div className="section-head left">
        <span className="eyebrow">Hola, {user.first_name || user.username}</span>
        <h1>Mi cuenta</h1>
      </div>
      <div className="tabs">
        <button className={tab === 'pedidos' ? 'active' : ''} onClick={() => setTab('pedidos')}>Mis pedidos</button>
        <button className={tab === 'datos' ? 'active' : ''} onClick={() => setTab('datos')}>Mis datos</button>
        <button className={tab === 'clave' ? 'active' : ''} onClick={() => setTab('clave')}>Contraseña</button>
      </div>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>

      {tab === 'pedidos' && (pedidos === null ? <Loader /> : pedidos.length === 0 ? (
        <EmptyState title="Todavía no tienes pedidos" action={<Link to="/catalogo" className="btn btn-dark">Comprar ahora</Link>} />
      ) : (
        <div className="orders">
          {pedidos.map((p) => (
            <Link to={`/pedido/${p.id}`} className="order-card" key={p.id}>
              <div><strong>Pedido #{p.id}</strong><span className="muted">{fecha(p.creado)}</span></div>
              <div className="muted">{p.items.map((i) => `${i.cantidad}× ${i.nombre}`).join(', ')}</div>
              <div className="order-foot">
                <StatusBadge estado={p.estado}>{p.estado_display}</StatusBadge>
                <strong>{money(p.total)}</strong>
              </div>
            </Link>
          ))}
        </div>
      ))}

      {tab === 'datos' && (
        <form className="panel narrow" onSubmit={guardar} noValidate>
          <div className="two">
            <Field label="Nombre" error={errors.first_name}><input value={form.first_name} onChange={(e) => set('first_name', e.target.value)} /></Field>
            <Field label="Apellidos" error={errors.last_name}><input value={form.last_name} onChange={(e) => set('last_name', e.target.value)} /></Field>
          </div>
          <div className="two">
            <Field label="Correo" error={errors.email}><input type="email" value={form.email} onChange={(e) => set('email', e.target.value)} /></Field>
            <Field label="Teléfono" error={errors.telefono}><input value={form.telefono} onChange={(e) => set('telefono', e.target.value)} /></Field>
          </div>
          <Field label="Dirección de envío"><input value={form.direccion} onChange={(e) => set('direccion', e.target.value)} /></Field>
          <div className="two">
            <Field label="Ciudad"><input value={form.ciudad} onChange={(e) => set('ciudad', e.target.value)} /></Field>
            <Field label="Departamento"><input value={form.departamento} onChange={(e) => set('departamento', e.target.value)} /></Field>
          </div>
          <button className="btn btn-dark">Actualizar información</button>
        </form>
      )}

      {tab === 'clave' && (
        <form className="panel narrow" onSubmit={cambiarClave} noValidate>
          <Field label="Contraseña actual" error={errors.password_actual}><input type="password" value={pass.password_actual} onChange={(e) => setPass({ ...pass, password_actual: e.target.value })} autoComplete="current-password" /></Field>
          <Field label="Nueva contraseña" error={errors.password} hint="Mínimo 8 caracteres, con letras y números."><input type="password" value={pass.password} onChange={(e) => setPass({ ...pass, password: e.target.value })} autoComplete="new-password" /></Field>
          <Field label="Confirmar nueva contraseña" error={errors.password2}><input type="password" value={pass.password2} onChange={(e) => setPass({ ...pass, password2: e.target.value })} autoComplete="new-password" /></Field>
          <button className="btn btn-dark">Cambiar contraseña</button>
        </form>
      )}
    </div>
  )
}

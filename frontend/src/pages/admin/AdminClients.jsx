import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader, Modal, Reintentar, StatusBadge } from '../../components/ui'
import { TIPOS_DOCUMENTO, errorDocumento, fecha, money } from '../../utils/format'

const VACIO = {
  tipo_documento: 'CC', numero_documento: '', nombres: '', apellidos: '', correo: '',
  telefono: '', direccion: '', ciudad: '', departamento: '',
}

/**
 * Clientes (HU-US-005). Un CLIENTE es la persona que compra; puede tener cuenta
 * en la web (usuario) o no, por ejemplo si compra en el local.
 */
export default function AdminClients() {
  const [q, setQ] = useState('')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [editando, setEditando] = useState(null)   // null = cerrado, 'nuevo' o el cliente
  const [form, setForm] = useState(VACIO)
  const [errors, setErrors] = useState({})
  const [guardando, setGuardando] = useState(false)

  function cargar(texto = q) {
    return api(`/admin/clientes/${texto ? `?q=${encodeURIComponent(texto)}` : ''}`).then(setItems).catch((e) => setError(e.message))
  }

  useEffect(() => {
    const t = setTimeout(() => cargar(q), 250)   // espera a que el usuario deje de escribir
    return () => clearTimeout(t)
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })) }

  function abrir(c = null) {
    setErrors({})
    setForm(c ? Object.fromEntries(Object.keys(VACIO).map((k) => [k, c[k] ?? ''])) : VACIO)
    setEditando(c || 'nuevo')
  }

  async function guardar(ev) {
    ev.preventDefault()
    const e = {}
    if (form.nombres.trim().length < 2) e.nombres = 'Escribe los nombres.'
    const doc = errorDocumento(form.tipo_documento, form.numero_documento)
    if (doc) e.numero_documento = doc
    if (form.telefono && !/^[0-9+\-\s()]{7,20}$/.test(form.telefono)) e.telefono = 'Teléfono no válido.'
    setErrors(e)
    if (Object.keys(e).length) return
    setGuardando(true)
    try {
      if (editando === 'nuevo') await api('/admin/clientes/', { method: 'POST', body: form })
      else await api(`/admin/clientes/${editando.id}/`, { method: 'PATCH', body: form })
      setMsg({ type: 'ok', text: editando === 'nuevo' ? 'Cliente registrado correctamente.' : 'Datos del cliente actualizados.' })
      setEditando(null)
      cargar()
    } catch (err) {
      setErrors(err.fields)
      setMsg({ type: 'error', text: err.message })
    } finally {
      setGuardando(false)
    }
  }

  async function eliminar(c) {
    const extra = c.tiene_cuenta ? ' Su cuenta web quedará desactivada.' : ''
    if (!window.confirm(`¿Mover a "${c.nombres} ${c.apellidos}" a la Papelera?${extra} Podrás restaurarlo desde Papelera.`)) return
    try {
      const r = await api(`/admin/clientes/${c.id}/`, { method: 'DELETE' })
      setMsg({ type: 'ok', text: r.detail })
      cargar()
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  return (
    <>
      <div className="page-head">
        <div><h1>Clientes</h1><p className="muted">Personas que compran, tengan o no cuenta en la web.</p></div>
        <button className="btn btn-gold" onClick={() => abrir()}>+ Registrar cliente</button>
      </div>
      <Alert>{error}</Alert>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>
      <div className="toolbar"><input placeholder="Buscar por nombre, documento, correo o usuario…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      {items === null ? (error ? <Reintentar /> : <Loader />) : items.length === 0 ? <EmptyState title="No hay clientes" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Cliente</th><th>Documento</th><th>Contacto</th><th>Cuenta web</th><th>Pedidos</th><th>Total comprado</th><th>Registro</th><th className="right">Acciones</th></tr></thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.id}>
                  <td><b>{`${c.nombres} ${c.apellidos}`.trim()}</b><br /><small className="muted">{c.ciudad || ''}</small></td>
                  <td>{c.numero_documento ? `${c.tipo_documento} ${c.numero_documento}` : <span className="muted">Sin documento</span>}</td>
                  <td>{c.correo || '—'}<br /><small className="muted">{c.telefono || ''}</small></td>
                  <td>{c.tiene_cuenta ? <StatusBadge estado="activo">{c.usuario_username}</StatusBadge> : <StatusBadge estado="oculto">Sin cuenta</StatusBadge>}</td>
                  <td>{c.total_pedidos}</td>
                  <td>{money(c.total_comprado)}</td>
                  <td>{fecha(c.creado)}</td>
                  <td className="row-actions right">
                    <button className="btn btn-ghost btn-sm" onClick={() => abrir(c)}>Editar</button>
                    <button className="btn btn-danger btn-sm" onClick={() => eliminar(c)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={editando !== null} title={editando === 'nuevo' ? 'Registrar cliente' : 'Editar cliente'} onClose={() => setEditando(null)}>
        <form onSubmit={guardar} noValidate>
          {editando === 'nuevo' && (
            <p className="hint-box">Para clientes que compran en el local, sin cuenta web. Si luego se registran en la página con el mismo documento, se les enlaza este cliente.</p>
          )}
          <div className="two">
            <Field label="Tipo de documento">
              <select value={form.tipo_documento} onChange={(e) => set('tipo_documento', e.target.value)}>
                {TIPOS_DOCUMENTO.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </Field>
            <Field label="Número de documento *" error={errors.numero_documento}>
              <input value={form.numero_documento} onChange={(e) => set('numero_documento', e.target.value)} />
            </Field>
          </div>
          <div className="two">
            <Field label="Nombres *" error={errors.nombres}><input value={form.nombres} onChange={(e) => set('nombres', e.target.value)} /></Field>
            <Field label="Apellidos" error={errors.apellidos}><input value={form.apellidos} onChange={(e) => set('apellidos', e.target.value)} /></Field>
          </div>
          <div className="two">
            <Field label="Correo" error={errors.correo}><input type="email" value={form.correo} onChange={(e) => set('correo', e.target.value)} /></Field>
            <Field label="Teléfono" error={errors.telefono}><input value={form.telefono} onChange={(e) => set('telefono', e.target.value)} inputMode="tel" /></Field>
          </div>
          <Field label="Dirección"><input value={form.direccion} onChange={(e) => set('direccion', e.target.value)} /></Field>
          <div className="two">
            <Field label="Ciudad"><input value={form.ciudad} onChange={(e) => set('ciudad', e.target.value)} /></Field>
            <Field label="Departamento"><input value={form.departamento} onChange={(e) => set('departamento', e.target.value)} /></Field>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setEditando(null)}>Cancelar</button>
            <button className="btn btn-dark" disabled={guardando}>{guardando ? 'Guardando…' : editando === 'nuevo' ? 'Registrar' : 'Guardar cambios'}</button>
          </div>
        </form>
      </Modal>
    </>
  )
}

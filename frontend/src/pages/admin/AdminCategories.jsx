import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader, Reintentar, StatusBadge } from '../../components/ui'

/** CRUD de categorías (HU-IN-010). */
export default function AdminCategories() {
  const [items, setItems] = useState(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '' })
  const [editId, setEditId] = useState(null)
  const [msg, setMsg] = useState({ type: '', text: '' })

  const cargar = () => api('/categorias/').then(setItems).catch((e) => setMsg({ type: 'error', text: e.message }))
  useEffect(() => { cargar() }, [])

  async function guardar(e) {
    e.preventDefault()
    if (form.nombre.trim().length < 2) return setMsg({ type: 'error', text: 'Escribe un nombre de categoría (mínimo 2 letras).' })
    try {
      if (editId) await api(`/categorias/${editId}/`, { method: 'PATCH', body: form })
      else await api('/categorias/', { method: 'POST', body: { ...form, activa: true } })
      setMsg({ type: 'ok', text: editId ? 'Categoría actualizada.' : 'Categoría creada.' })
      setForm({ nombre: '', descripcion: '' })
      setEditId(null)
      cargar()
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    }
    return undefined
  }

  async function accion(promesa, ok) {
    try { await promesa; setMsg({ type: 'ok', text: ok }); cargar() } catch (e) { setMsg({ type: 'error', text: e.message }) }
  }

  return (
    <>
      <div className="page-head"><div><h1>Categorías</h1><p className="muted">Organiza el catálogo por colecciones.</p></div></div>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>
      <form className="card inline-form" onSubmit={guardar}>
        <Field label={editId ? 'Editar nombre' : 'Nueva categoría'}><input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Ej. Pulseras tejidas" /></Field>
        <Field label="Descripción (opcional)"><input value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /></Field>
        <div className="row-actions">
          <button className="btn btn-dark">{editId ? 'Guardar' : 'Crear'}</button>
          {editId && <button type="button" className="btn btn-ghost" onClick={() => { setEditId(null); setForm({ nombre: '', descripcion: '' }) }}>Cancelar</button>}
        </div>
      </form>

      {items === null ? (msg.type === 'error' ? <Reintentar /> : <Loader />) : items.length === 0 ? <EmptyState title="Aún no hay categorías" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Nombre</th><th>Productos</th><th>Estado</th><th className="right">Acciones</th></tr></thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.id}>
                  <td><b>{c.nombre}</b><br /><small className="muted">{c.descripcion}</small></td>
                  <td>{c.total_productos || 'Sin productos asociados'}</td>
                  <td>{c.activa ? <StatusBadge estado="activo">Visible</StatusBadge> : <StatusBadge estado="oculto">Oculta</StatusBadge>}</td>
                  <td className="row-actions right">
                    <button className="btn btn-ghost btn-sm" onClick={() => { setEditId(c.id); setForm({ nombre: c.nombre, descripcion: c.descripcion }) }}>Editar</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => accion(api(`/categorias/${c.id}/`, { method: 'PATCH', body: { activa: !c.activa } }), 'Visibilidad actualizada.')}>{c.activa ? 'Ocultar' : 'Mostrar'}</button>
                    <button className="btn btn-danger btn-sm" onClick={() => window.confirm(`¿Eliminar "${c.nombre}"? Sus productos quedarán sin categoría.`) && accion(api(`/categorias/${c.id}/`, { method: 'DELETE' }), 'Categoría eliminada.')}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

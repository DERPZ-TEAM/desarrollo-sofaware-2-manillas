import { useEffect, useState } from 'react'
import { api } from '../../api'

export default function AdminCategories() {
  const [items, setItems] = useState([])
  const [nombre, setNombre] = useState('')
  const [editId, setEditId] = useState(null)
  const [error, setError] = useState('')

  async function load() {
    setItems(await api('/categorias/'))
  }
  useEffect(() => { load() }, [])

  async function save(e) {
    e.preventDefault()
    setError('')
    if (nombre.trim().length < 2) return setError('Escribe un nombre de categoría.')
    try {
      if (editId) await api(`/categorias/${editId}/`, { method: 'PATCH', body: { nombre } })
      else await api('/categorias/', { method: 'POST', body: { nombre, activa: true } })
      setNombre('')
      setEditId(null)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function toggle(c) {
    await api(`/categorias/${c.id}/`, { method: 'PATCH', body: { activa: !c.activa } })
    await load()
  }

  async function remove(c) {
    if (!confirm(`¿Eliminar ${c.nombre}? Los productos quedan sin categoría.`)) return
    await api(`/categorias/${c.id}/`, { method: 'DELETE' })
    await load()
  }

  return (
    <>
      <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 22 }}>Categorías</h1>
      {error && <div className="error">{error}</div>}
      <form className="panel" onSubmit={save} style={{ display: 'flex', gap: 12, alignItems: 'end' }}>
        <div className="field" style={{ flex: 1, margin: 0 }}>
          <label>{editId ? 'Editar' : 'Nueva categoría'}</label>
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Ej. Pulseras tejidas" />
        </div>
        <button className="btn btn-dark">{editId ? 'Guardar' : 'Crear'}</button>
      </form>
      <table>
        <thead><tr><th>Nombre</th><th>Productos</th><th>Visible</th><th></th></tr></thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.id}>
              <td>{c.nombre}</td>
              <td>{c.total_productos}</td>
              <td>{c.activa ? 'Sí' : 'Oculta'}</td>
              <td className="row-actions">
                <button className="btn btn-ghost btn-sm" onClick={() => { setEditId(c.id); setNombre(c.nombre) }}>Editar</button>
                <button className="btn btn-ghost btn-sm" onClick={() => toggle(c)}>{c.activa ? 'Ocultar' : 'Mostrar'}</button>
                <button className="btn btn-danger btn-sm" onClick={() => remove(c)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

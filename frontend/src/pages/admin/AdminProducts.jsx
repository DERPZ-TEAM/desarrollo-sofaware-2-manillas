import { useEffect, useState } from 'react'
import { api, apiForm } from '../../api'

const empty = { nombre: '', descripcion: '', precio: '', stock: 0, categoria: '', activo: true, imagen: null }

export default function AdminProducts() {
  const [items, setItems] = useState([])
  const [cats, setCats] = useState([])
  const [form, setForm] = useState(empty)
  const [editId, setEditId] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  async function load() {
    const [prods, categorias] = await Promise.all([api('/productos/'), api('/categorias/')])
    setItems(prods)
    setCats(categorias)
  }

  useEffect(() => { load().catch((e) => setError(e.message)) }, [])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  function startEdit(p) {
    setEditId(p.id)
    setForm({
      nombre: p.nombre,
      descripcion: p.descripcion,
      precio: p.precio,
      stock: p.stock,
      categoria: p.categoria || '',
      activo: p.activo,
      imagen: null,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function save(e) {
    e.preventDefault()
    setError('')
    setMsg('')
    if (form.nombre.trim().length < 3) return setError('El nombre debe tener al menos 3 caracteres.')
    if (form.descripcion.trim().length < 10) return setError('La descripción debe tener al menos 10 caracteres.')
    if (Number(form.precio) <= 0) return setError('El precio debe ser mayor a 0.')
    const fd = new FormData()
    fd.append('nombre', form.nombre.trim())
    fd.append('descripcion', form.descripcion.trim())
    fd.append('precio', form.precio)
    fd.append('stock', form.stock)
    fd.append('activo', form.activo ? 'true' : 'false')
    if (form.categoria) fd.append('categoria', form.categoria)
    if (form.imagen) fd.append('imagen', form.imagen)
    try {
      if (editId) await apiForm(`/productos/${editId}/`, fd, 'PATCH')
      else await apiForm('/productos/', fd, 'POST')
      setForm(empty)
      setEditId(null)
      setMsg(editId ? 'Producto actualizado en la base de datos y en la tienda.' : 'Producto creado.')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function toggle(p) {
    await api(`/productos/${p.id}/visibilidad/`, { method: 'POST' })
    await load()
  }

  async function remove(p) {
    if (!confirm(`¿Eliminar ${p.nombre}? Se quitará de PostgreSQL y de la tienda.`)) return
    await api(`/productos/${p.id}/`, { method: 'DELETE' })
    await load()
  }

  return (
    <>
      <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 22 }}>Productos</h1>
      {error && <div className="error">{error}</div>}
      {msg && <div className="ok">{msg}</div>}
      <form className="panel product-form" onSubmit={save}>
        <h3>{editId ? 'Editar producto' : 'Nuevo producto'}</h3>
        <div className="field"><label>Nombre</label><input value={form.nombre} onChange={(e) => set('nombre', e.target.value)} /></div>
        <div className="field"><label>Descripción</label><textarea rows="3" value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} /></div>
        <div className="two">
          <div className="field"><label>Precio</label><input type="number" min="1" value={form.precio} onChange={(e) => set('precio', e.target.value)} /></div>
          <div className="field"><label>Stock</label><input type="number" min="0" value={form.stock} onChange={(e) => set('stock', e.target.value)} /></div>
        </div>
        <div className="two">
          <div className="field">
            <label>Categoría</label>
            <select value={form.categoria} onChange={(e) => set('categoria', e.target.value)}>
              <option value="">Sin categoría</option>
              {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </div>
          <div className="field"><label>Imagen</label><input type="file" accept="image/*" onChange={(e) => set('imagen', e.target.files[0])} /></div>
        </div>
        <label className="switch">
          <input type="checkbox" checked={form.activo} onChange={(e) => set('activo', e.target.checked)} /> Visible en la tienda
        </label>
        <div className="row-actions">
          <button className="btn btn-dark">{editId ? 'Guardar cambios' : 'Publicar'}</button>
          {editId && <button type="button" className="btn btn-ghost" onClick={() => { setEditId(null); setForm(empty) }}>Cancelar</button>}
        </div>
      </form>
      <table>
        <thead>
          <tr><th>Pieza</th><th>Categoría</th><th>Precio</th><th>Stock</th><th>Visible</th><th></th></tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id}>
              <td>{p.nombre}</td>
              <td>{p.categoria_nombre || '—'}</td>
              <td>{p.precio}</td>
              <td>{p.stock}</td>
              <td>{p.activo ? 'Sí' : 'Oculto'}</td>
              <td className="row-actions">
                <button className="btn btn-ghost btn-sm" onClick={() => startEdit(p)}>Editar</button>
                <button className="btn btn-ghost btn-sm" onClick={() => toggle(p)}>{p.activo ? 'Ocultar' : 'Mostrar'}</button>
                <button className="btn btn-danger btn-sm" onClick={() => remove(p)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

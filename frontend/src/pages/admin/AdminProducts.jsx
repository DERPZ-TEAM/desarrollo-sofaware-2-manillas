import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader, Modal, StatusBadge } from '../../components/ui'
import { IMAGEN_RESPALDO, money } from '../../utils/format'

const VACIO = {
  nombre: '', descripcion: '', precio: '', stock: 0, stock_minimo: 3, categoria: '', activo: true,
  tipo_oro: '', quilates: '', peso_gramos: '', talla_cm: '', elaboracion: '', imagen: null, quitar_imagen: false,
}
const MAX_MB = 5

/** CRUD de productos (HU-IN-006, 007, 008, 009, 010). */
export default function AdminProducts() {
  const [items, setItems] = useState(null)
  const [cats, setCats] = useState([])
  const [opciones, setOpciones] = useState({ tipos_oro: [], quilates: [], elaboracion: [] })
  const [filtro, setFiltro] = useState({ q: '', categoria: '', activo: '' })
  const [form, setForm] = useState(VACIO)
  const [editando, setEditando] = useState(null)   // null = cerrado, 'nuevo' o el producto
  const [preview, setPreview] = useState('')
  const [errors, setErrors] = useState({})
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [saving, setSaving] = useState(false)

  const cargar = useCallback(async () => {
    const qs = new URLSearchParams(Object.entries(filtro).filter(([, v]) => v)).toString()
    try {
      setItems(await api(`/productos/${qs ? `?${qs}` : ''}`))
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
      setItems([])
    }
  }, [filtro])

  useEffect(() => { cargar() }, [cargar])
  useEffect(() => {
    api('/categorias/').then(setCats).catch(() => {})
    api('/productos/opciones/').then(setOpciones).catch(() => {})
  }, [])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })) }

  function abrir(p = null) {
    setErrors({})
    if (p) {
      setForm({
        ...VACIO, ...Object.fromEntries(Object.keys(VACIO).map((k) => [k, p[k] ?? VACIO[k]])),
        categoria: p.categoria || '', imagen: null, quitar_imagen: false,
      })
      setPreview(p.imagen_url || '')
    } else {
      setForm(VACIO)
      setPreview('')
    }
    setEditando(p || 'nuevo')
  }

  function elegirImagen(file) {
    if (!file) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setErrors((e) => ({ ...e, imagen: 'Formato no permitido. Usa JPG, PNG o WEBP.' }))
      return
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setErrors((e) => ({ ...e, imagen: `La imagen supera ${MAX_MB} MB.` }))
      return
    }
    set('imagen', file)
    set('quitar_imagen', false)
    setPreview(URL.createObjectURL(file))
  }

  function validar() {
    const e = {}
    if (form.nombre.trim().length < 3) e.nombre = 'Mínimo 3 caracteres.'
    if (form.descripcion.trim().length < 10) e.descripcion = 'Mínimo 10 caracteres.'
    if (!(Number(form.precio) > 0)) e.precio = 'Debe ser mayor a 0.'
    if (!(Number(form.stock) >= 0) || !Number.isInteger(Number(form.stock))) e.stock = 'Número entero ≥ 0.'
    if (!form.categoria) e.categoria = 'Selecciona una categoría.'
    return e
  }

  async function guardar(ev) {
    ev.preventDefault()
    const e = validar()
    setErrors(e)
    if (Object.keys(e).length) return
    // FormData = formulario "multipart", necesario para enviar archivos (la imagen)
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => {
      if (k === 'imagen') { if (v) fd.append('imagen', v); return }
      fd.append(k, typeof v === 'boolean' ? String(v) : v ?? '')
    })
    setSaving(true)
    try {
      if (editando === 'nuevo') await api('/productos/', { method: 'POST', body: fd })
      else await api(`/productos/${editando.id}/`, { method: 'PATCH', body: fd })
      setMsg({ type: 'ok', text: editando === 'nuevo' ? 'Producto registrado correctamente.' : 'Información actualizada correctamente.' })
      setEditando(null)
      cargar()
    } catch (err) {
      setErrors(err.fields)
      setMsg({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  async function toggle(p) {
    try { await api(`/productos/${p.id}/visibilidad/`, { method: 'POST' }); cargar() } catch (e) { setMsg({ type: 'error', text: e.message }) }
  }

  async function eliminar(p) {
    if (!window.confirm(`¿Eliminar "${p.nombre}" del catálogo? Esta acción no se puede deshacer.`)) return
    try {
      const r = await api(`/productos/${p.id}/`, { method: 'DELETE' })
      setMsg({ type: 'ok', text: r.detail })
      cargar()
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  return (
    <>
      <div className="page-head">
        <div><h1>Productos</h1><p className="muted">Crea, edita y publica las piezas del catálogo.</p></div>
        <button className="btn btn-gold" onClick={() => abrir()}>+ Nuevo producto</button>
      </div>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>

      <div className="toolbar">
        <input placeholder="Buscar por nombre…" value={filtro.q} onChange={(e) => setFiltro({ ...filtro, q: e.target.value })} />
        <select value={filtro.categoria} onChange={(e) => setFiltro({ ...filtro, categoria: e.target.value })}>
          <option value="">Todas las categorías</option>
          {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select>
        <select value={filtro.activo} onChange={(e) => setFiltro({ ...filtro, activo: e.target.value })}>
          <option value="">Visibles y ocultos</option>
          <option value="true">Solo visibles</option>
          <option value="false">Solo ocultos</option>
        </select>
      </div>

      {items === null ? <Loader /> : items.length === 0 ? (
        <EmptyState title="No hay productos" action={<button className="btn btn-dark" onClick={() => abrir()}>Registrar el primero</button>} />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Pieza</th><th>Categoría</th><th>Material</th><th>Precio</th><th>Stock</th><th>Estado</th><th className="right">Acciones</th></tr></thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td><div className="cell-product"><img src={p.imagen_url || IMAGEN_RESPALDO} alt="" /><b>{p.nombre}</b></div></td>
                  <td>{p.categoria_nombre || <span className="muted">Sin categoría</span>}</td>
                  <td>{[p.tipo_oro_display, p.quilates && `${p.quilates}k`].filter(Boolean).join(' · ') || '—'}</td>
                  <td>{money(p.precio)}</td>
                  <td><StatusBadge estado={p.estado_stock}>{p.stock}</StatusBadge></td>
                  <td>{p.activo ? <StatusBadge estado="activo">Visible</StatusBadge> : <StatusBadge estado="oculto">Oculto</StatusBadge>}</td>
                  <td className="row-actions right">
                    <button className="btn btn-ghost btn-sm" onClick={() => abrir(p)}>Editar</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => toggle(p)}>{p.activo ? 'Ocultar' : 'Publicar'}</button>
                    <button className="btn btn-danger btn-sm" onClick={() => eliminar(p)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={editando !== null} wide title={editando === 'nuevo' ? 'Nuevo producto' : 'Editar producto'} onClose={() => setEditando(null)}>
        <form className="product-form" onSubmit={guardar} noValidate>
          <div className="form-cols">
            <div>
              <Field label="Nombre *" error={errors.nombre}><input value={form.nombre} onChange={(e) => set('nombre', e.target.value)} /></Field>
              <Field label="Descripción *" error={errors.descripcion}><textarea rows="3" value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} /></Field>
              <div className="three">
                <Field label="Precio (COP) *" error={errors.precio}><input type="number" min="1" value={form.precio} onChange={(e) => set('precio', e.target.value)} /></Field>
                <Field label="Stock *" error={errors.stock}><input type="number" min="0" value={form.stock} onChange={(e) => set('stock', e.target.value)} /></Field>
                <Field label="Stock mínimo" error={errors.stock_minimo} hint="Alerta de bajo stock"><input type="number" min="0" value={form.stock_minimo} onChange={(e) => set('stock_minimo', e.target.value)} /></Field>
              </div>
              <Field label="Categoría *" error={errors.categoria}>
                <select value={form.categoria} onChange={(e) => set('categoria', e.target.value)}>
                  <option value="">Selecciona…</option>
                  {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
              </Field>
              <h4 className="form-section">Ficha técnica</h4>
              <div className="three">
                <Field label="Tipo de oro" error={errors.tipo_oro}>
                  <select value={form.tipo_oro} onChange={(e) => set('tipo_oro', e.target.value)}>
                    <option value="">—</option>
                    {opciones.tipos_oro.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </Field>
                <Field label="Quilates" error={errors.quilates}>
                  <select value={form.quilates || ''} onChange={(e) => set('quilates', e.target.value)}>
                    <option value="">—</option>
                    {opciones.quilates.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </Field>
                <Field label="Elaboración" error={errors.elaboracion}>
                  <select value={form.elaboracion} onChange={(e) => set('elaboracion', e.target.value)}>
                    <option value="">—</option>
                    {opciones.elaboracion.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </Field>
              </div>
              <div className="two">
                <Field label="Peso (g)" error={errors.peso_gramos}><input type="number" step="0.01" min="0" value={form.peso_gramos || ''} onChange={(e) => set('peso_gramos', e.target.value)} /></Field>
                <Field label="Talla (cm)" error={errors.talla_cm}><input type="number" step="0.5" min="10" max="30" value={form.talla_cm || ''} onChange={(e) => set('talla_cm', e.target.value)} /></Field>
              </div>
            </div>
            <div>
              <Field label="Imagen" error={errors.imagen} hint={`JPG, PNG o WEBP · máx. ${MAX_MB} MB`}>
                <div className="image-drop">
                  <img src={preview || IMAGEN_RESPALDO} alt="Vista previa" />
                  <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => elegirImagen(e.target.files[0])} />
                </div>
              </Field>
              {preview && editando !== 'nuevo' && !form.imagen && (
                <label className="check"><input type="checkbox" checked={form.quitar_imagen} onChange={(e) => set('quitar_imagen', e.target.checked)} /> Quitar imagen actual</label>
              )}
              <label className="switch">
                <input type="checkbox" checked={form.activo} onChange={(e) => set('activo', e.target.checked)} />
                <span /> Visible en la tienda
              </label>
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setEditando(null)}>Cancelar</button>
            <button className="btn btn-dark" disabled={saving}>{saving ? 'Guardando…' : editando === 'nuevo' ? 'Registrar' : 'Actualizar información'}</button>
          </div>
        </form>
      </Modal>
    </>
  )
}

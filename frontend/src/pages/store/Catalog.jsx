import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import ProductCard from '../../components/ProductCard'
import { Alert, EmptyState, Loader } from '../../components/ui'
import useAddToCart from '../../utils/useAddToCart'

const FILTROS_VACIOS = { q: '', categoria: '', precio_min: '', precio_max: '', tipo_oro: '', talla: '', orden: 'recientes', disponibles: '' }

/**
 * Catálogo con búsqueda y filtros (HU-VE-011, 013, 014, 015, HU-IN-049).
 * Los filtros se guardan en la URL (?q=...&tipo_oro=...) para poder compartir el enlace.
 */
export default function Catalog() {
  const [params, setParams] = useSearchParams()
  const [form, setForm] = useState({ ...FILTROS_VACIOS, ...Object.fromEntries(params) })
  const [productos, setProductos] = useState(null)
  const [categorias, setCategorias] = useState([])
  const [opciones, setOpciones] = useState({ tipos_oro: [], tallas: [] })
  const [error, setError] = useState('')
  const [verFiltros, setVerFiltros] = useState(false)   // solo afecta a celulares
  const { add, addingId, mensaje, clearMensaje } = useAddToCart()

  useEffect(() => {
    api('/categorias/', { auth: false }).then(setCategorias).catch(() => {})
    api('/productos/opciones/', { auth: false }).then(setOpciones).catch(() => {})
  }, [])

  // Cada vez que cambian los parámetros de la URL, pedimos los productos
  useEffect(() => {
    setProductos(null)
    setError('')
    const qs = params.toString()
    api(`/productos/${qs ? `?${qs}` : ''}`, { auth: false })
      .then(setProductos)
      .catch((e) => { setError(e.message); setProductos([]) })
  }, [params])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  function aplicar(e, cambios = {}) {
    e?.preventDefault()
    const datos = { ...form, ...cambios }
    if (datos.precio_min && datos.precio_max && Number(datos.precio_min) > Number(datos.precio_max)) {
      setError('El precio mínimo no puede ser mayor que el máximo.')
      return
    }
    setForm(datos)
    setError('')
    const limpio = Object.fromEntries(Object.entries(datos).filter(([k, v]) => v && !(k === 'orden' && v === 'recientes')))
    setParams(limpio)
  }

  // Cuántos filtros están aplicados (para mostrarlo en el botón de celular)
  const activos = [...params.keys()].filter((k) => k !== 'orden').length

  function limpiar() {
    setForm(FILTROS_VACIOS)
    setParams({})
  }

  return (
    <div className="wrap section">
      <div className="section-head left">
        <span className="eyebrow">Catálogo</span>
        <h1>Todas nuestras piezas</h1>
      </div>

      <button type="button" className="btn btn-ghost filters-toggle" onClick={() => setVerFiltros(!verFiltros)}>
        {verFiltros ? 'Ocultar filtros' : 'Filtrar y ordenar'}
        {activos > 0 && <span className="filters-count">{activos}</span>}
      </button>

      <div className="catalog">
        <aside className={`filters ${verFiltros ? 'open' : ''}`}>
          <form onSubmit={aplicar}>
            <label className="field">
              <span className="field-label">Buscar por nombre</span>
              <input value={form.q} onChange={(e) => set('q', e.target.value)} placeholder="Ej. pulsera imperial" />
            </label>

            <div className="filter-group">
              <span className="field-label">Categoría</span>
              <div className="chips">
                <button type="button" className={!form.categoria ? 'chip active' : 'chip'} onClick={() => aplicar(null, { categoria: '' })}>Todas</button>
                {categorias.map((c) => (
                  <button type="button" key={c.id}
                    className={String(form.categoria) === String(c.id) ? 'chip active' : 'chip'}
                    onClick={() => aplicar(null, { categoria: String(c.id) })}>
                    {c.nombre} <small>({c.total_productos})</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
              <span className="field-label">Precio (COP)</span>
              <div className="two">
                <input type="number" min="0" placeholder="Mínimo" value={form.precio_min} onChange={(e) => set('precio_min', e.target.value)} />
                <input type="number" min="0" placeholder="Máximo" value={form.precio_max} onChange={(e) => set('precio_max', e.target.value)} />
              </div>
            </div>

            <label className="field">
              <span className="field-label">Tipo de oro</span>
              <select value={form.tipo_oro} onChange={(e) => aplicar(null, { tipo_oro: e.target.value })}>
                <option value="">Todos</option>
                {opciones.tipos_oro.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </label>

            <label className="field">
              <span className="field-label">Talla</span>
              <select value={form.talla} onChange={(e) => aplicar(null, { talla: e.target.value })}>
                <option value="">Todas</option>
                {opciones.tallas.map((t) => <option key={t} value={t}>{t} cm</option>)}
              </select>
            </label>

            <label className="field">
              <span className="field-label">Ordenar por</span>
              <select value={form.orden} onChange={(e) => aplicar(null, { orden: e.target.value })}>
                <option value="recientes">Más recientes</option>
                <option value="precio_asc">Precio: menor a mayor</option>
                <option value="precio_desc">Precio: mayor a menor</option>
                <option value="nombre">Nombre A-Z</option>
              </select>
            </label>

            <label className="check">
              <input type="checkbox" checked={form.disponibles === 'true'} onChange={(e) => aplicar(null, { disponibles: e.target.checked ? 'true' : '' })} />
              Solo disponibles
            </label>

            <button className="btn btn-dark btn-block">Buscar</button>
            <button type="button" className="btn btn-link btn-block" onClick={limpiar}>Limpiar</button>
          </form>
        </aside>

        <section>
          <Alert type={mensaje.type} onClose={clearMensaje}>{mensaje.text}</Alert>
          <Alert onClose={() => setError('')}>{error}</Alert>
          {productos === null ? <Loader text="Buscando piezas..." /> : productos.length === 0 ? (
            <EmptyState title="No encontramos piezas" action={<button className="btn btn-dark" onClick={limpiar}>Ver todo</button>}>
              No hay productos disponibles con esos criterios.
            </EmptyState>
          ) : (
            <>
              <p className="muted">{productos.length} {productos.length === 1 ? 'pieza' : 'piezas'}</p>
              <div className="grid grid-3">
                {productos.map((p) => (
                  <ProductCard key={p.id} producto={p} onAdd={add} adding={addingId === p.id} />
                ))}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  )
}

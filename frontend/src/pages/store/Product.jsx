import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader } from '../../components/ui'
import { IMAGEN_RESPALDO, money } from '../../utils/format'
import useAddToCart from '../../utils/useAddToCart'

/** Detalle del producto + ficha técnica (HU-VE-12, HU-PR-035). */
export default function Product() {
  const { id } = useParams()
  const [p, setP] = useState(undefined)
  const [cantidad, setCantidad] = useState(1)
  const { add, addingId, mensaje, clearMensaje } = useAddToCart()

  useEffect(() => {
    setP(undefined)
    api(`/productos/${id}/`, { auth: false }).then(setP).catch(() => setP(null))
  }, [id])

  if (p === undefined) return <div className="wrap section"><Loader text="Cargando pieza..." /></div>
  if (p === null) {
    return (
      <div className="wrap section">
        <EmptyState title="Producto no disponible" action={<Link to="/catalogo" className="btn btn-dark">Volver al catálogo</Link>}>
          Esta pieza fue retirada o no existe.
        </EmptyState>
      </div>
    )
  }

  const ficha = [
    ['Material', p.tipo_oro_display],
    ['Quilates', p.quilates && `${p.quilates}k`],
    ['Peso', p.peso_gramos && `${Number(p.peso_gramos)} g`],
    ['Talla', p.talla_cm && `${Number(p.talla_cm)} cm`],
    ['Elaboración', p.elaboracion_display],
    ['Categoría', p.categoria_nombre],
  ]
  const faltantes = ficha.filter(([, v]) => !v).map(([k]) => k.toLowerCase())
  const agotado = p.stock === 0

  return (
    <div className="wrap section product-detail">
      <div className="detail-media">
        <img src={p.imagen_url || IMAGEN_RESPALDO} alt={p.nombre} onError={(e) => { e.currentTarget.src = IMAGEN_RESPALDO }} />
      </div>
      <div className="detail-info">
        <Link to="/catalogo" className="back">← Catálogo</Link>
        <span className="eyebrow">{p.categoria_nombre || 'GoldBracelets'}</span>
        <h1>{p.nombre}</h1>
        <p className="detail-price">{money(p.precio)}</p>
        <p className="detail-desc">{p.descripcion}</p>

        <p className={`stock-note stock-${p.estado_stock}`}>
          {agotado ? 'Agotado por ahora' : p.estado_stock === 'bajo' ? `¡Solo quedan ${p.stock}!` : `${p.stock} disponibles`}
        </p>

        <Alert type={mensaje.type} onClose={clearMensaje}>
          {mensaje.text}{mensaje.type !== 'error' && <> · <Link to="/carrito">Ver carrito</Link></>}
        </Alert>

        <div className="buy-row">
          <div className="qty">
            <button type="button" onClick={() => setCantidad(Math.max(1, cantidad - 1))}>−</button>
            <span>{cantidad}</span>
            <button type="button" onClick={() => setCantidad(Math.min(p.stock || 1, cantidad + 1))}>+</button>
          </div>
          <button className="btn btn-dark" disabled={agotado || addingId === p.id} onClick={() => add(p, cantidad)}>
            {agotado ? 'Agotado' : 'Añadir al carrito'}
          </button>
        </div>

        <div className="spec-sheet">
          <h3>Ficha técnica</h3>
          <dl>
            {ficha.filter(([, v]) => v).map(([k, v]) => (
              <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
            ))}
          </dl>
          {faltantes.length > 0 && <p className="muted small">Datos no registrados para esta pieza: {faltantes.join(', ')}.</p>}
        </div>
      </div>
    </div>
  )
}

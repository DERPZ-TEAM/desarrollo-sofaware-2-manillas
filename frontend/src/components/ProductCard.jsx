import { Link } from 'react-router-dom'
import { IMAGEN_RESPALDO, money } from '../utils/format'

/** Tarjeta de producto del catálogo (vista del cliente). */
export default function ProductCard({ producto, onAdd, adding }) {
  const agotado = producto.stock === 0
  return (
    <article className="product-card">
      <Link to={`/producto/${producto.id}`} className="product-media">
        <img
          src={producto.imagen_url || IMAGEN_RESPALDO}
          alt={producto.nombre}
          loading="lazy"
          onError={(e) => { e.currentTarget.src = IMAGEN_RESPALDO }}
        />
        {agotado && <span className="ribbon">Agotado</span>}
        {!agotado && producto.estado_stock === 'bajo' && <span className="ribbon ribbon-gold">Últimas unidades</span>}
      </Link>
      <div className="product-info">
        <span className="eyebrow">{producto.categoria_nombre || 'GoldBracelets'}</span>
        <Link to={`/producto/${producto.id}`}><h3>{producto.nombre}</h3></Link>
        <p className="product-specs">
          {[producto.tipo_oro_display, producto.quilates && `${producto.quilates}k`, producto.talla_cm && `${Number(producto.talla_cm)} cm`]
            .filter(Boolean).join(' · ') || 'Pieza artesanal'}
        </p>
        <div className="product-foot">
          <span className="price">{money(producto.precio)}</span>
          <button
            type="button"
            className="btn btn-gold btn-sm"
            disabled={agotado || adding}
            onClick={() => onAdd(producto)}
          >
            {agotado ? 'Agotado' : adding ? 'Agregando…' : 'Añadir'}
          </button>
        </div>
      </div>
    </article>
  )
}

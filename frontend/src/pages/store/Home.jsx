import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import ProductCard from '../../components/ProductCard'
import { Alert, Loader } from '../../components/ui'
import useAddToCart from '../../utils/useAddToCart'

/** Portada de la tienda (landing). */
export default function Home() {
  const [destacados, setDestacados] = useState(null)
  const [categorias, setCategorias] = useState([])
  const [error, setError] = useState('')
  const { add, addingId, mensaje, clearMensaje } = useAddToCart()

  useEffect(() => {
    Promise.all([api('/productos/destacados/', { auth: false }), api('/categorias/', { auth: false })])
      .then(([prods, cats]) => { setDestacados(prods); setCategorias(cats) })
      .catch((e) => { setError(e.message); setDestacados([]) })
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow eyebrow-light">Colección 2026</span>
          <h1>La belleza de tu esencia en <em>cada detalle</em></h1>
          <p>Pulseras tejidas a mano, brazaletes y cadenas en oro de 14k y 18k. Diseñadas para acompañarte todos los días.</p>
          <div className="hero-actions">
            <Link to="/catalogo" className="btn btn-gold">Explorar catálogo</Link>
            <Link to="/registro" className="btn btn-outline-light">Crear cuenta</Link>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="ring ring-1" /><div className="ring ring-2" /><div className="ring ring-3" />
        </div>
      </section>

      <section className="perks wrap">
        <div><b>Oro certificado</b><span>10k, 14k, 18k y 24k</span></div>
        <div><b>Hecho a mano</b><span>Tejidos artesanales</span></div>
        <div><b>Precio por mayor</b><span>5% · 10% · 15% desde 6 piezas</span></div>
        <div><b>Envío nacional</b><span>Con número de guía</span></div>
      </section>

      {categorias.length > 0 && (
        <section className="wrap section">
          <div className="section-head">
            <span className="eyebrow">Colecciones</span>
            <h2>Encuentra tu estilo</h2>
          </div>
          <div className="cat-tiles">
            {categorias.map((c) => (
              <Link key={c.id} to={`/catalogo?categoria=${c.id}`} className="cat-tile">
                <span>{c.nombre}</span>
                <small>{c.total_productos ? `${c.total_productos} piezas` : 'Sin productos asociados'}</small>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="wrap section">
        <div className="section-head">
          <span className="eyebrow">Lo más deseado</span>
          <h2>Piezas destacadas</h2>
        </div>
        <Alert type={mensaje.type} onClose={clearMensaje}>{mensaje.text}</Alert>
        <Alert>{error}</Alert>
        {destacados === null ? <Loader /> : (
          <div className="grid">
            {destacados.map((p) => (
              <ProductCard key={p.id} producto={p} onAdd={add} adding={addingId === p.id} />
            ))}
          </div>
        )}
        <div className="center"><Link to="/catalogo" className="btn btn-dark">Ver todo el catálogo</Link></div>
      </section>

      <section className="banner">
        <div className="wrap banner-inner">
          <div>
            <h2>¿Compras para tu negocio?</h2>
            <p>Lleva 6, 12 o 24 piezas y el descuento se aplica solo en tu carrito.</p>
          </div>
          <Link to="/catalogo" className="btn btn-gold">Comprar por mayor</Link>
        </div>
      </section>
    </>
  )
}

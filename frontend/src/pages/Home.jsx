import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function Home() {
  const [categorias, setCategorias] = useState([])
  const [productos, setProductos] = useState([])
  const [cat, setCat] = useState('')
  const { isCustomer, refreshCart } = useAuth()
  const navigate = useNavigate()

  async function load(categoria = '') {
    const qs = categoria ? `?categoria=${categoria}` : ''
    const [cats, prods] = await Promise.all([
      api('/categorias/'),
      api(`/productos/${qs}`),
    ])
    setCategorias(cats)
    setProductos(prods)
  }

  useEffect(() => { load(cat).catch(() => {}) }, [cat])

  async function add(id) {
    if (!isCustomer) {
      navigate('/ingresar')
      return
    }
    await api('/carrito/', { method: 'POST', body: { producto_id: id, cantidad: 1 } })
    refreshCart()
  }

  return (
    <>
      <section className="hero">
        <div>
          <h1>La belleza de tu esencia en <em>cada detalle</em></h1>
          <p>Pulseras, cadenas y piezas en tono oro pensadas para acompañarte todos los días.</p>
          <a className="btn btn-dark" href="#catalogo" style={{ marginTop: 18 }}>Comprar ahora</a>
        </div>
      </section>
      <section className="section wrap" id="catalogo">
        <div className="cats">
          <button className={!cat ? 'active' : ''} onClick={() => setCat('')}>Todo</button>
          {categorias.map((c) => (
            <button key={c.id} className={String(cat) === String(c.id) ? 'active' : ''} onClick={() => setCat(c.id)}>
              {c.nombre}
            </button>
          ))}
        </div>
        <div className="grid">
          {productos.map((p) => (
            <article className="card" key={p.id}>
              <Link to={`/producto/${p.id}`}>
                <img src={p.imagen_url || 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?auto=format&fit=crop&w=600&q=80'} alt={p.nombre} />
                <h3>{p.nombre}</h3>
                <div className="meta">{p.categoria_nombre || 'GoldBracelets'}</div>
                <div className="price">{money(p.precio)}</div>
              </Link>
              <button className="btn btn-gold btn-sm" style={{ marginTop: 10 }} onClick={() => add(p.id)}>Añadir</button>
            </article>
          ))}
        </div>
        {productos.length === 0 && <p className="hint">Aún no hay piezas visibles. El administrador puede publicarlas desde el panel.</p>}
      </section>
    </>
  )
}

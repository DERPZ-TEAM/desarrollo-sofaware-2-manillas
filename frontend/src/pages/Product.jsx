import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../AuthContext'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function Product() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [msg, setMsg] = useState('')
  const { isCustomer, refreshCart } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    api(`/productos/${id}/`).then(setP).catch(() => setP(null))
  }, [id])

  if (!p) return <div className="wrap section">Cargando pieza...</div>

  async function add() {
    if (!isCustomer) return navigate('/ingresar')
    await api('/carrito/', { method: 'POST', body: { producto_id: p.id, cantidad: 1 } })
    await refreshCart()
    setMsg('Añadida a tu bolso.')
  }

  return (
    <div className="wrap section" style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 40 }}>
      <img className="thumb" src={p.imagen_url || ''} alt={p.nombre} />
      <div>
        <p className="meta">{p.categoria_nombre}</p>
        <h1 className="serif" style={{ fontSize: 48, margin: '0 0 8px' }}>{p.nombre}</h1>
        <h2>{money(p.precio)}</h2>
        <p>{p.descripcion}</p>
        <p className="hint">Disponibles: {p.stock}</p>
        {msg && <div className="ok">{msg}</div>}
        <button className="btn btn-dark" onClick={add}>Añadir al bolso</button>
      </div>
    </div>
  )
}

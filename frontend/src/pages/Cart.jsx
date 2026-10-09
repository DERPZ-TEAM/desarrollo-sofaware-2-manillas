import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../AuthContext'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function Cart() {
  const [cart, setCart] = useState(null)
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const { refreshCart } = useAuth()

  async function load() {
    const data = await api('/carrito/')
    setCart(data)
    refreshCart()
  }

  useEffect(() => { load().catch((e) => setError(e.message)) }, [])

  async function patch(id, cantidad) {
    const data = await api(`/carrito/items/${id}/`, { method: 'PATCH', body: { cantidad } })
    setCart(data)
    refreshCart()
  }

  async function remove(id) {
    const data = await api(`/carrito/items/${id}/`, { method: 'DELETE' })
    setCart(data)
    refreshCart()
  }

  async function checkout() {
    setError('')
    try {
      await api('/checkout/', { method: 'POST', body: {} })
      setMsg('Pedido confirmado. Gracias por tu compra.')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  if (!cart) return <div className="wrap section">Cargando bolso...</div>

  return (
    <div className="wrap section">
      <h1 className="serif" style={{ fontSize: 42 }}>Tu bolso</h1>
      {error && <div className="error">{error}</div>}
      {msg && <div className="ok">{msg}</div>}
      {cart.items.length === 0 && <p className="hint">Aún no has añadido piezas.</p>}
      {cart.items.map((item) => (
        <div className="cart-row" key={item.id}>
          <img className="thumb" style={{ aspectRatio: '1/1' }} src={item.producto.imagen_url || ''} alt="" />
          <div>
            <strong>{item.producto.nombre}</strong>
            <div className="meta">{money(item.producto.precio)}</div>
          </div>
          <div className="qty">
            <button onClick={() => patch(item.id, item.cantidad - 1)}>-</button>
            <span>{item.cantidad}</span>
            <button onClick={() => patch(item.id, item.cantidad + 1)}>+</button>
          </div>
          <div>
            <div>{money(item.subtotal)}</div>
            <button className="btn btn-ghost btn-sm" onClick={() => remove(item.id)}>Quitar</button>
          </div>
        </div>
      ))}
      {cart.items.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24, alignItems: 'center' }}>
          <h2>Total {money(cart.total)}</h2>
          <button className="btn btn-dark" onClick={checkout}>Finalizar compra</button>
        </div>
      )}
    </div>
  )
}

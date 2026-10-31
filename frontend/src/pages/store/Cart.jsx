import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader, Reintentar } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { IMAGEN_RESPALDO, money } from '../../utils/format'

/** Carrito de compras (HU-CO-016, 017, 018). */
export default function Cart() {
  const [cart, setCart] = useState(null)
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [busy, setBusy] = useState(false)
  const { setCartCount } = useAuth()

  function actualizar(data) {
    setCart(data)
    setCartCount(data.resumen.cantidad_items)
    if (data.detail) setMsg({ type: 'info', text: data.detail })
  }

  useEffect(() => {
    api('/carrito/').then((d) => { delete d.detail; actualizar(d) })
      .catch((e) => setMsg({ type: 'error', text: e.message }))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function ejecutar(promesa) {
    setBusy(true)
    try {
      actualizar(await promesa)
    } catch (e) {
      setMsg({ type: 'error', text: e.message })   // el carrito anterior se conserva
    } finally {
      setBusy(false)
    }
  }

  const cambiar = (item, cantidad) => ejecutar(api(`/carrito/items/${item.id}/`, { method: 'PATCH', body: { cantidad } }))
  const quitar = (item) => ejecutar(api(`/carrito/items/${item.id}/`, { method: 'DELETE' }))
  const vaciar = () => window.confirm('¿Vaciar todo el carrito?') && ejecutar(api('/carrito/', { method: 'DELETE' }))

  if (!cart) return <div className="wrap section"><Alert type={msg.type}>{msg.text}</Alert>{msg.type === 'error' ? <Reintentar /> : <Loader text="Cargando carrito..." />}</div>

  const { resumen } = cart
  const faltan = resumen.cantidad_items < 6 ? 6 - resumen.cantidad_items : resumen.cantidad_items < 12 ? 12 - resumen.cantidad_items : resumen.cantidad_items < 24 ? 24 - resumen.cantidad_items : 0

  return (
    <div className="wrap section">
      <div className="section-head left">
        <span className="eyebrow">Tu selección</span>
        <h1>Carrito de compras</h1>
      </div>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>

      {cart.items.length === 0 ? (
        <EmptyState title="Tu carrito está vacío" action={<Link to="/catalogo" className="btn btn-dark">Ir al catálogo</Link>}>
          Total: {money(0)}. Añade piezas para comenzar tu pedido.
        </EmptyState>
      ) : (
        <div className="cart-layout">
          <div className="cart-list">
            {cart.items.map((item) => (
              <div className="cart-row" key={item.id}>
                <img src={item.producto.imagen_url || IMAGEN_RESPALDO} alt="" />
                <div className="cart-name">
                  <Link to={`/producto/${item.producto.id}`}><strong>{item.producto.nombre}</strong></Link>
                  <span className="muted">{money(item.producto.precio)} c/u · {item.producto.stock} en stock</span>
                </div>
                <div className="qty">
                  <button disabled={busy} onClick={() => cambiar(item, item.cantidad - 1)} aria-label="Restar">−</button>
                  <span>{item.cantidad}</span>
                  <button disabled={busy || item.cantidad >= item.producto.stock} onClick={() => cambiar(item, item.cantidad + 1)} aria-label="Sumar">+</button>
                </div>
                <strong className="cart-sub">{money(item.subtotal)}</strong>
                <button className="icon-btn" disabled={busy} onClick={() => quitar(item)} aria-label="Eliminar">×</button>
              </div>
            ))}
            <button className="btn btn-link" onClick={vaciar} disabled={busy}>Vaciar carrito</button>
          </div>

          <aside className="summary">
            <h3>Resumen</h3>
            <div className="sum-row"><span>Piezas</span><span>{resumen.cantidad_items}</span></div>
            <div className="sum-row"><span>Subtotal</span><span>{money(resumen.subtotal)}</span></div>
            {Number(resumen.descuento) > 0 && (
              <div className="sum-row gold"><span>Descuento por mayor ({Number(resumen.porcentaje_descuento)}%)</span><span>−{money(resumen.descuento)}</span></div>
            )}
            <div className="sum-row total"><span>Total</span><span>{money(resumen.total)}</span></div>
            {faltan > 0 && <p className="hint-box">Agrega {faltan} pieza(s) más para obtener un mayor descuento por volumen.</p>}
            <Link to="/checkout" className="btn btn-gold btn-block">Continuar con la compra</Link>
          </aside>
        </div>
      )}
    </div>
  )
}

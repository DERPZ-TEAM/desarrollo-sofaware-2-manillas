import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader, StatusBadge } from '../../components/ui'
import { fecha, money } from '../../utils/format'

const PASOS = ['pendiente', 'confirmado', 'enviado', 'entregado']

// Qué debe hacer el cliente según el método de pago elegido
const INSTRUCCIONES_PAGO = {
  contraentrega: 'Pagas en efectivo cuando recibas tu pedido.',
  transferencia: 'Un asesor te contactará al teléfono registrado con los datos de la cuenta. Tu pedido se confirma cuando recibamos el pago.',
  nequi: 'Un asesor te contactará al teléfono registrado con el número Nequi / Daviplata. Tu pedido se confirma cuando recibamos el pago.',
  tarjeta: 'Pago de demostración: no se realizó ningún cobro real.',
}

/** Comprobante / detalle de un pedido (HU-VE-022, HU-PE-023). Se puede imprimir. */
export default function OrderDetail() {
  const { id } = useParams()
  const { state } = useLocation()
  const [pedido, setPedido] = useState(undefined)
  const [msg, setMsg] = useState({ type: state?.nuevo ? 'ok' : '', text: state?.nuevo ? '¡Compra confirmada! Guarda este comprobante.' : '' })

  useEffect(() => { api(`/pedidos/${id}/`).then(setPedido).catch(() => setPedido(null)) }, [id])

  async function cancelar() {
    if (!window.confirm('¿Seguro que quieres cancelar este pedido?')) return
    try {
      const data = await api(`/pedidos/${id}/cancelar/`, { method: 'POST' })
      setPedido(data)
      setMsg({ type: 'ok', text: data.detail })
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    }
  }

  if (pedido === undefined) return <div className="wrap section"><Loader /></div>
  if (pedido === null) return <div className="wrap section"><EmptyState title="Pedido no encontrado" action={<Link className="btn btn-dark" to="/cuenta">Mis pedidos</Link>} /></div>

  const paso = PASOS.indexOf(pedido.estado)
  return (
    <div className="wrap section receipt-page">
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>
      <div className="receipt">
        <header className="receipt-head">
          <div>
            <div className="brand"><span className="brand-mark">GB</span><span>GOLD<b>BRACELETS</b></span></div>
            <p className="muted">Comprobante de compra</p>
          </div>
          <div className="right">
            <h2>Pedido #{pedido.id}</h2>
            <p className="muted">{fecha(pedido.creado, true)}</p>
            <StatusBadge estado={pedido.estado}>{pedido.estado_display}</StatusBadge>
          </div>
        </header>

        {pedido.estado !== 'cancelado' && (
          <ol className="tracker">
            {PASOS.map((p, i) => <li key={p} className={i <= paso ? 'done' : ''}>{p[0].toUpperCase() + p.slice(1)}</li>)}
          </ol>
        )}

        <div className="receipt-grid">
          <div>
            <h4>Envío</h4>
            <p>{pedido.nombre_destinatario}<br />{pedido.direccion_envio}<br />{pedido.ciudad}, {pedido.departamento}<br />Tel. {pedido.telefono_contacto}</p>
            {pedido.numero_guia && <p><b>Guía:</b> {pedido.transportadora} {pedido.numero_guia}</p>}
          </div>
          <div>
            <h4>Pago</h4>
            <p>{pedido.metodo_pago_display}</p>
            {pedido.estado === 'pendiente' && INSTRUCCIONES_PAGO[pedido.metodo_pago] && (
              <p className="hint-box">{INSTRUCCIONES_PAGO[pedido.metodo_pago]}</p>
            )}
            {pedido.notas && <><h4>Notas</h4><p>{pedido.notas}</p></>}
          </div>
        </div>

        <table className="table">
          <thead><tr><th>Producto</th><th>Cant.</th><th>Precio</th><th className="right">Subtotal</th></tr></thead>
          <tbody>
            {pedido.items.map((i) => (
              <tr key={i.id}><td>{i.nombre}</td><td>{i.cantidad}</td><td>{money(i.precio)}</td><td className="right">{money(i.subtotal)}</td></tr>
            ))}
          </tbody>
        </table>
        <div className="receipt-totals">
          <div><span>Subtotal</span><span>{money(pedido.subtotal)}</span></div>
          {Number(pedido.descuento) > 0 && <div><span>Descuento por volumen</span><span>−{money(pedido.descuento)}</span></div>}
          <div className="total"><span>Total</span><span>{money(pedido.total)}</span></div>
        </div>
      </div>
      <div className="row-actions no-print">
        <button className="btn btn-dark" onClick={() => window.print()}>Imprimir / Guardar PDF</button>
        {['pendiente', 'confirmado'].includes(pedido.estado) && <button className="btn btn-danger" onClick={cancelar}>Cancelar pedido</button>}
        <Link to="/cuenta" className="btn btn-link">Mis pedidos</Link>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader, Modal, Reintentar, StatusBadge } from '../../components/ui'
import { ESTADOS_PEDIDO, fecha, money } from '../../utils/format'

/** Gestión de pedidos: historial, estados y guía de envío (HU-PE-024, 025, 050, HU-IN-029). */
export default function AdminOrders() {
  const [filtro, setFiltro] = useState({ estado: '', q: '' })
  const [items, setItems] = useState(null)
  const [sel, setSel] = useState(null)
  const [envio, setEnvio] = useState({ transportadora: '', numero_guia: '' })
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [modalMsg, setModalMsg] = useState('')

  const cargar = () => {
    const qs = new URLSearchParams(Object.entries(filtro).filter(([, v]) => v)).toString()
    return api(`/admin/pedidos/${qs ? `?${qs}` : ''}`).then(setItems).catch((e) => setMsg({ type: 'error', text: e.message }))
  }
  useEffect(() => { cargar() }, [filtro]) // eslint-disable-line react-hooks/exhaustive-deps

  function abrir(p) {
    setSel(p)
    setModalMsg('')
    setEnvio({ transportadora: p.transportadora, numero_guia: p.numero_guia })
  }

  async function actualizar(body) {
    setModalMsg('')
    try {
      const data = await api(`/admin/pedidos/${sel.id}/`, { method: 'PATCH', body })
      setSel(data)
      setMsg({ type: 'ok', text: data.detail })
      cargar()
    } catch (e) {
      setModalMsg(e.message)
    }
  }

  return (
    <>
      <div className="page-head"><div><h1>Pedidos</h1><p className="muted">Historial completo de ventas y su estado de entrega.</p></div></div>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>
      <div className="toolbar">
        <input placeholder="Buscar por #, cliente o correo…" value={filtro.q} onChange={(e) => setFiltro({ ...filtro, q: e.target.value })} />
        <select value={filtro.estado} onChange={(e) => setFiltro({ ...filtro, estado: e.target.value })}>
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS_PEDIDO).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      {items === null ? (msg.type === 'error' ? <Reintentar /> : <Loader />) : items.length === 0 ? <EmptyState title="No hay pedidos registrados" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>#</th><th>Fecha</th><th>Cliente</th><th>Pago</th><th>Total</th><th>Estado</th><th className="right" /></tr></thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td><b>#{p.id}</b></td>
                  <td>{fecha(p.creado, true)}</td>
                  <td>{p.usuario_nombre}<br /><small className="muted">{p.usuario_email}</small></td>
                  <td>{p.metodo_pago_display}</td>
                  <td>{money(p.total)}</td>
                  <td><StatusBadge estado={p.estado}>{p.estado_display}</StatusBadge></td>
                  <td className="right"><button className="btn btn-ghost btn-sm" onClick={() => abrir(p)}>Gestionar</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={Boolean(sel)} wide title={sel ? `Pedido #${sel.id}` : ''} onClose={() => setSel(null)}>
        {sel && (
          <div className="order-admin">
            <Alert>{modalMsg}</Alert>
            <div className="receipt-grid">
              <div>
                <h4>Cliente</h4>
                <p>{sel.usuario_nombre} ({sel.usuario_username})<br />{sel.usuario_email}</p>
                <h4>Envío</h4>
                <p>{sel.nombre_destinatario || '—'}<br />{sel.direccion_envio}<br />{sel.ciudad} {sel.departamento}<br />Tel. {sel.telefono_contacto || '—'}</p>
              </div>
              <div>
                <h4>Estado actual</h4>
                <p><StatusBadge estado={sel.estado}>{sel.estado_display}</StatusBadge></p>
                <h4>Cambiar a</h4>
                {sel.estados_siguientes.length === 0 ? <p className="muted">Este pedido ya está finalizado.</p> : (
                  <div className="row-actions">
                    {sel.estados_siguientes.map((e) => (
                      <button key={e} className={`btn btn-sm ${e === 'cancelado' ? 'btn-danger' : 'btn-dark'}`}
                        onClick={() => (e !== 'cancelado' || window.confirm('¿Cancelar el pedido? El stock se devolverá al inventario.')) && actualizar({ estado: e, ...envio })}>
                        {ESTADOS_PEDIDO[e]}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <h4 className="form-section">Información de envío</h4>
            <div className="two">
              <Field label="Transportadora"><input value={envio.transportadora} onChange={(e) => setEnvio({ ...envio, transportadora: e.target.value })} placeholder="Servientrega, Coordinadora…" /></Field>
              <Field label="Número de guía" hint="Obligatorio para marcar como enviado"><input value={envio.numero_guia} onChange={(e) => setEnvio({ ...envio, numero_guia: e.target.value })} /></Field>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => actualizar(envio)}>Guardar datos de envío</button>

            <table className="table compact" style={{ marginTop: 18 }}>
              <thead><tr><th>Producto</th><th>Cant.</th><th>Precio</th><th className="right">Subtotal</th></tr></thead>
              <tbody>
                {sel.items.map((i) => <tr key={i.id}><td>{i.nombre}</td><td>{i.cantidad}</td><td>{money(i.precio)}</td><td className="right">{money(i.subtotal)}</td></tr>)}
              </tbody>
            </table>
            <div className="receipt-totals">
              <div><span>Subtotal</span><span>{money(sel.subtotal)}</span></div>
              {Number(sel.descuento) > 0 && <div><span>Descuento</span><span>−{money(sel.descuento)}</span></div>}
              <div className="total"><span>Total</span><span>{money(sel.total)}</span></div>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}

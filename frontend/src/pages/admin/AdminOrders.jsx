import { useEffect, useState } from 'react'
import { api } from '../../api'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function AdminOrders() {
  const [items, setItems] = useState([])
  useEffect(() => { api('/admin/pedidos/').then(setItems) }, [])

  async function change(id, estado) {
    await api(`/admin/pedidos/${id}/`, { method: 'PATCH', body: { estado } })
    setItems(await api('/admin/pedidos/'))
  }

  return (
    <>
      <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 22 }}>Pedidos</h1>
      <table>
        <thead><tr><th>#</th><th>Cliente</th><th>Total</th><th>Estado</th></tr></thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id}>
              <td>{p.id}</td>
              <td>{p.usuario_username}<br /><small>{p.usuario_email}</small></td>
              <td>{money(p.total)}</td>
              <td>
                <select value={p.estado} onChange={(e) => change(p.id, e.target.value)}>
                  <option value="pendiente">Pendiente</option>
                  <option value="confirmado">Confirmado</option>
                  <option value="enviado">Enviado</option>
                  <option value="entregado">Entregado</option>
                  <option value="cancelado">Cancelado</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

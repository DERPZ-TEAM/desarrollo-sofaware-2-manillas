import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, Loader, StatusBadge } from '../../components/ui'
import { fecha, money } from '../../utils/format'

/** Escritorio del administrador: indicadores + alertas de stock + pedidos recientes. */
export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { api('/admin/dashboard/').then(setData).catch((e) => setError(e.message)) }, [])

  if (error) return <Alert>{error}</Alert>
  if (!data) return <Loader text="Cargando escritorio..." />

  const stats = [
    ['Ventas totales', money(data.ventas), 'gold'],
    ['Ventas del mes', money(data.ventas_mes)],
    ['Pedidos', data.pedidos, null, `${data.pedidos_pendientes} pendientes`],
    ['Clientes', data.clientes],
    ['Productos', data.productos, null, `${data.productos_visibles} visibles`],
    ['Unidades en inventario', data.unidades_en_inventario],
  ]

  return (
    <>
      <div className="page-head">
        <div><h1>Escritorio</h1><p className="muted">Resumen de la tienda en tiempo real.</p></div>
        <Link to="/admin/productos" className="btn btn-gold">+ Nuevo producto</Link>
      </div>

      <div className="stats">
        {stats.map(([label, value, tone, extra]) => (
          <div className={`stat ${tone ? `stat-${tone}` : ''}`} key={label}>
            <span>{label}</span><b>{value}</b>{extra && <small>{extra}</small>}
          </div>
        ))}
      </div>

      <div className="dash-grid">
        <section className="card">
          <div className="card-head"><h3>Alertas de stock</h3><Link to="/admin/inventario">Ver inventario →</Link></div>
          {data.alertas_stock.length === 0 ? <p className="muted">Todo el inventario está por encima del mínimo.</p> : (
            <ul className="alert-list">
              {data.alertas_stock.map((p) => (
                <li key={p.id}>
                  <span>{p.nombre}</span>
                  <StatusBadge estado={p.estado_stock}>{p.stock === 0 ? 'Agotado' : `${p.stock} / mín. ${p.stock_minimo}`}</StatusBadge>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-head"><h3>Pedidos recientes</h3><Link to="/admin/pedidos">Ver todos →</Link></div>
          {data.pedidos_recientes.length === 0 ? <p className="muted">Todavía no hay pedidos.</p> : (
            <table className="table compact">
              <tbody>
                {data.pedidos_recientes.map((p) => (
                  <tr key={p.id}>
                    <td>#{p.id}</td>
                    <td>{p.usuario_nombre}<br /><small className="muted">{fecha(p.creado)}</small></td>
                    <td><StatusBadge estado={p.estado}>{p.estado_display}</StatusBadge></td>
                    <td className="right">{money(p.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </>
  )
}

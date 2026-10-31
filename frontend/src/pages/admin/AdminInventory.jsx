import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader, Reintentar, StatusBadge } from '../../components/ui'
import { money } from '../../utils/format'

const ETIQUETA = { agotado: 'Agotado', bajo: 'Bajo stock', ok: 'Suficiente' }

/** Estado del inventario y alertas de stock mínimo (HU-IN-028, HU-IN-048). */
export default function AdminInventory() {
  const [estado, setEstado] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [edit, setEdit] = useState({})

  const cargar = () => api(`/admin/inventario/${estado ? `?estado=${estado}` : ''}`).then(setData).catch((e) => setError(e.message))
  useEffect(() => { setData(null); cargar() }, [estado]) // eslint-disable-line react-hooks/exhaustive-deps

  async function ajustar(p) {
    const stock = Number(edit[p.id])
    if (!Number.isInteger(stock) || stock < 0) return setError('El stock debe ser un número entero mayor o igual a 0.')
    try {
      await api(`/productos/${p.id}/`, { method: 'PATCH', body: { stock } })
      setEdit((e) => ({ ...e, [p.id]: undefined }))
      cargar()
    } catch (e) { setError(e.message) }
    return undefined
  }

  return (
    <>
      <div className="page-head"><div><h1>Inventario</h1><p className="muted">Existencias, valor del inventario y alertas.</p></div></div>
      <Alert onClose={() => setError('')}>{error}</Alert>
      {data && (
        <div className="stats">
          <div className="stat"><span>Unidades</span><b>{data.resumen.unidades}</b></div>
          <div className="stat stat-gold"><span>Valor del inventario</span><b>{money(data.resumen.valor)}</b></div>
          <div className="stat stat-warn"><span>Bajo stock</span><b>{data.resumen.bajos}</b></div>
          <div className="stat stat-danger"><span>Agotados</span><b>{data.resumen.agotados}</b></div>
        </div>
      )}
      <div className="tabs">
        {[['', 'Todos'], ['agotado', 'Agotados'], ['bajo', 'Bajo stock'], ['ok', 'Suficiente']].map(([v, l]) => (
          <button key={v} className={estado === v ? 'active' : ''} onClick={() => setEstado(v)}>{l}</button>
        ))}
      </div>
      {data === null ? (error ? <Reintentar /> : <Loader />) : data.productos.length === 0 ? <EmptyState title="No hay productos en este estado" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Producto</th><th>Categoría</th><th>Stock</th><th>Mínimo</th><th>Estado</th><th>Valor</th><th className="right">Ajustar stock</th></tr></thead>
            <tbody>
              {data.productos.map((p) => (
                <tr key={p.id}>
                  <td><b>{p.nombre}</b></td>
                  <td>{p.categoria_nombre || '—'}</td>
                  <td>{p.stock}</td>
                  <td>{p.stock_minimo}</td>
                  <td><StatusBadge estado={p.estado_stock}>{ETIQUETA[p.estado_stock]}</StatusBadge></td>
                  <td>{money(p.stock * p.precio)}</td>
                  <td className="right">
                    <div className="inline-edit">
                      <input type="number" min="0" placeholder={p.stock} value={edit[p.id] ?? ''} onChange={(e) => setEdit({ ...edit, [p.id]: e.target.value })} />
                      <button className="btn btn-ghost btn-sm" disabled={edit[p.id] === undefined || edit[p.id] === ''} onClick={() => ajustar(p)}>Guardar</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

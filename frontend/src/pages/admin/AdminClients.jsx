import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader } from '../../components/ui'
import { fecha, money } from '../../utils/format'

/** Consulta de clientes registrados, en orden alfabético (HU-US-005). */
export default function AdminClients() {
  const [q, setQ] = useState('')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const t = setTimeout(() => {
      api(`/admin/clientes/${q ? `?q=${encodeURIComponent(q)}` : ''}`).then(setItems).catch((e) => setError(e.message))
    }, 250)   // espera a que el usuario deje de escribir
    return () => clearTimeout(t)
  }, [q])

  return (
    <>
      <div className="page-head"><div><h1>Clientes</h1><p className="muted">Cuentas registradas en la tienda.</p></div></div>
      <Alert>{error}</Alert>
      <div className="toolbar"><input placeholder="Buscar por nombre, usuario o correo…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      {items === null ? <Loader /> : items.length === 0 ? <EmptyState title="No hay clientes" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Cliente</th><th>Usuario</th><th>Correo</th><th>Teléfono</th><th>Ciudad</th><th>Pedidos</th><th>Total comprado</th><th>Registro</th></tr></thead>
            <tbody>
              {items.map((u) => (
                <tr key={u.id}>
                  <td><b>{`${u.first_name} ${u.last_name}`.trim() || '—'}</b></td>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.telefono || '—'}</td>
                  <td>{u.ciudad || '—'}</td>
                  <td>{u.total_pedidos}</td>
                  <td>{money(u.total_comprado)}</td>
                  <td>{fecha(u.date_joined)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

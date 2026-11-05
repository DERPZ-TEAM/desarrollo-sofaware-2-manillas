import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader, Reintentar, StatusBadge } from '../../components/ui'
import { fecha } from '../../utils/format'

/**
 * Usuarios: todas las CUENTAS de la página. La columna "¿Es cliente?" dice
 * cuáles ya compraron (esas personas también aparecen en Clientes).
 */
export default function AdminUsers() {
  const [q, setQ] = useState('')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const t = setTimeout(() => {
      setError('')
      api(`/admin/usuarios/${q ? `?q=${encodeURIComponent(q)}` : ''}`).then(setItems).catch((e) => setError(e.message))
    }, 250)   // espera a que el usuario deje de escribir
    return () => clearTimeout(t)
  }, [q])

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Usuarios</h1>
          <p className="muted">Cuentas para entrar a la página. Un usuario pasa a ser cliente cuando hace su primera compra.</p>
        </div>
      </div>
      <Alert>{error}</Alert>
      <div className="toolbar"><input placeholder="Buscar por usuario, nombre o correo…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
      {items === null ? (error ? <Reintentar /> : <Loader />) : items.length === 0 ? <EmptyState title="No hay usuarios" /> : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Usuario</th><th>Nombre</th><th>Correo</th><th>Rol</th><th>¿Es cliente?</th><th>Pedidos</th><th>Registro</th><th>Último ingreso</th></tr></thead>
            <tbody>
              {items.map((u) => (
                <tr key={u.id}>
                  <td><b>{u.username}</b>{!u.is_active && <><br /><small className="muted">Desactivado</small></>}</td>
                  <td>{`${u.first_name} ${u.last_name}`.trim() || '—'}</td>
                  <td>{u.email || '—'}</td>
                  <td>{u.rol === 'admin' ? 'Administrador' : 'Cliente web'}</td>
                  <td>
                    {u.rol === 'admin' ? <span className="muted">No aplica</span>
                      : u.es_cliente ? <StatusBadge estado="activo">Sí, ya compró</StatusBadge>
                        : <StatusBadge estado="oculto">Aún no compra</StatusBadge>}
                  </td>
                  <td>{u.total_pedidos}</td>
                  <td>{fecha(u.date_joined)}</td>
                  <td>{u.last_login ? fecha(u.last_login, true) : 'Nunca'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

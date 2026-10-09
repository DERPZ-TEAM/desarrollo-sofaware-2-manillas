import { useEffect, useState } from 'react'
import { api } from '../../api'

export default function AdminClients() {
  const [items, setItems] = useState([])
  useEffect(() => { api('/admin/clientes/').then(setItems) }, [])
  return (
    <>
      <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 22 }}>Clientes</h1>
      <table>
        <thead><tr><th>Usuario</th><th>Nombre</th><th>Correo</th><th>Teléfono</th></tr></thead>
        <tbody>
          {items.map((u) => (
            <tr key={u.id}>
              <td>{u.username}</td>
              <td>{u.first_name} {u.last_name}</td>
              <td>{u.email}</td>
              <td>{u.telefono || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

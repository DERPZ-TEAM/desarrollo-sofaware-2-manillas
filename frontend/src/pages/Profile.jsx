import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../AuthContext'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function Profile() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    telefono: user?.telefono || '',
  })
  const [pedidos, setPedidos] = useState([])
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api('/pedidos/').then(setPedidos).catch(() => {})
  }, [])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  async function save(e) {
    e.preventDefault()
    setError('')
    try {
      const data = await api('/auth/me/', { method: 'PUT', body: form })
      setUser(data)
      localStorage.setItem('gb_user', JSON.stringify(data))
      setMsg('Datos actualizados.')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="wrap section">
      <h1 className="serif" style={{ fontSize: 42 }}>Mi cuenta</h1>
      {msg && <div className="ok">{msg}</div>}
      {error && <div className="error">{error}</div>}
      <form onSubmit={save} className="product-form" style={{ maxWidth: 520 }}>
        <div className="two">
          <div className="field"><label>Nombre</label><input value={form.first_name} onChange={(e) => set('first_name', e.target.value)} /></div>
          <div className="field"><label>Apellidos</label><input value={form.last_name} onChange={(e) => set('last_name', e.target.value)} /></div>
        </div>
        <div className="field"><label>Correo</label><input value={form.email} onChange={(e) => set('email', e.target.value)} /></div>
        <div className="field"><label>Teléfono</label><input value={form.telefono} onChange={(e) => set('telefono', e.target.value)} /></div>
        <button className="btn btn-dark">Guardar</button>
      </form>
      <h2 className="serif" style={{ marginTop: 40 }}>Pedidos</h2>
      {pedidos.length === 0 && <p className="hint">Todavía no tienes pedidos.</p>}
      {pedidos.map((p) => (
        <div className="panel" key={p.id}>
          <strong>Pedido #{p.id}</strong> · {p.estado} · {money(p.total)}
          <ul>
            {p.items.map((i) => (
              <li key={i.id}>{i.cantidad} × {i.nombre}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

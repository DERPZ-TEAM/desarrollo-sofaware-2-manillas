import { useEffect, useState } from 'react'
import { api } from '../../api'

function money(v) {
  return Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  useEffect(() => { api('/admin/dashboard/').then(setData) }, [])
  if (!data) return <p>Cargando escritorio...</p>
  return (
    <>
      <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: 22 }}>Escritorio</h1>
      <p>Los cambios que hagas aquí se guardan en PostgreSQL y se reflejan al instante en la tienda.</p>
      <div className="stats">
        <div className="stat"><span>Productos</span><b>{data.productos}</b></div>
        <div className="stat"><span>Visibles en tienda</span><b>{data.productos_visibles}</b></div>
        <div className="stat"><span>Categorías</span><b>{data.categorias}</b></div>
        <div className="stat"><span>Clientes</span><b>{data.clientes}</b></div>
        <div className="stat"><span>Pedidos</span><b>{data.pedidos}</b></div>
        <div className="stat"><span>Ventas</span><b>{money(data.ventas)}</b></div>
      </div>
      <div className="panel" style={{ marginTop: 18 }}>
        <h3>Pedidos recientes</h3>
        {data.pedidos_recientes.length === 0 && <p>Todavía no hay pedidos.</p>}
        {data.pedidos_recientes.map((p) => (
          <div key={p.id}>#{p.id} · {p.usuario_username} · {p.estado} · {money(p.total)}</div>
        ))}
      </div>
    </>
  )
}

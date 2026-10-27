import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader } from '../../components/ui'
import { money } from '../../utils/format'

// Qué muestra cada reporte (se ve debajo de las pestañas)
const DESCRIPCIONES = {
  ingresos: 'Dinero vendido en el rango de fechas, agrupado por día, mes o año. No cuenta pedidos cancelados.',
  vendidos: 'Ranking de las piezas que más se vendieron en el rango, por unidades o por ingresos.',
  sinventas: 'Piezas que NO se vendieron ni una vez en el rango de fechas: sirven para decidir promociones o retirar productos.',
}

function hace(dias) {
  const d = new Date()
  d.setDate(d.getDate() - dias)
  // Fecha LOCAL en formato AAAA-MM-DD (toISOString usaría la hora UTC y podría dar "mañana")
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Reportes: ingresos por día/mes/año, más vendidos y sin ventas (HU-RE-030, 031, 045, 046). */
export default function AdminReports() {
  const [tab, setTab] = useState('ingresos')
  const [rango, setRango] = useState({ desde: hace(365), hasta: hace(0) })
  const [periodo, setPeriodo] = useState('mes')
  const [criterio, setCriterio] = useState('cantidad')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let vigente = true   // si el usuario cambia de pestaña antes de que responda, ignoramos la respuesta vieja
    if (rango.desde > rango.hasta) { setError('La fecha inicial no puede ser mayor que la final.'); return undefined }
    setError('')
    setData(null)
    const base = `desde=${rango.desde}&hasta=${rango.hasta}`
    const url = {
      ingresos: `/admin/reportes/ingresos/?periodo=${periodo}&${base}`,
      vendidos: `/admin/reportes/mas-vendidos/?criterio=${criterio}&${base}`,
      sinventas: `/admin/reportes/sin-ventas/?${base}`,
    }[tab]
    // Guardamos junto a los datos a qué pestaña pertenecen
    api(url)
      .then((d) => { if (vigente) setData({ ...d, pestana: tab }) })
      .catch((e) => { if (vigente) setError(e.message) })
    return () => { vigente = false }
  }, [tab, rango, periodo, criterio])

  // Solo mostramos datos que correspondan a la pestaña abierta. Antes, al cambiar de
  // pestaña se intentaba dibujar "Sin ventas" con los datos de "Ingresos" y la página fallaba.
  const vista = data && data.pestana === tab ? data : null
  const max = vista?.filas ? Math.max(1, ...vista.filas.map((f) => Number(f.ingresos))) : 1

  return (
    <>
      <div className="page-head"><div><h1>Reportes</h1><p className="muted">Analiza ventas e inventario por periodo.</p></div>
        <button className="btn btn-ghost no-print" onClick={() => window.print()}>Imprimir</button></div>

      <div className="tabs">
        <button className={tab === 'ingresos' ? 'active' : ''} onClick={() => setTab('ingresos')}>Ingresos</button>
        <button className={tab === 'vendidos' ? 'active' : ''} onClick={() => setTab('vendidos')}>Más vendidos</button>
        <button className={tab === 'sinventas' ? 'active' : ''} onClick={() => setTab('sinventas')}>Sin ventas</button>
      </div>

      <p className="muted small">{DESCRIPCIONES[tab]}</p>

      <div className="toolbar">
        <label>Desde <input type="date" value={rango.desde} onChange={(e) => setRango({ ...rango, desde: e.target.value })} /></label>
        <label>Hasta <input type="date" value={rango.hasta} onChange={(e) => setRango({ ...rango, hasta: e.target.value })} /></label>
        {tab === 'ingresos' && (
          <select value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
            <option value="dia">Por día</option><option value="mes">Por mes</option><option value="anio">Por año</option>
          </select>
        )}
        {tab === 'vendidos' && (
          <select value={criterio} onChange={(e) => setCriterio(e.target.value)}>
            <option value="cantidad">Por unidades</option><option value="ingresos">Por ingresos</option>
          </select>
        )}
      </div>

      <Alert>{error}</Alert>
      {!vista ? (!error && <Loader />) : (
        <>
          {tab === 'ingresos' && (vista.filas.length === 0 ? <EmptyState title="No existen ventas en el periodo seleccionado" /> : (
            <div className="card">
              <div className="stats">
                <div className="stat stat-gold"><span>Ingresos del periodo</span><b>{money(vista.total_ingresos)}</b></div>
                <div className="stat"><span>Pedidos</span><b>{vista.total_pedidos}</b></div>
              </div>
              <div className="bars">
                {vista.filas.map((f) => (
                  <div className="bar-row" key={f.periodo}>
                    <span className="bar-label">{f.periodo}</span>
                    <div className="bar-track"><div className="bar-fill" style={{ width: `${(Number(f.ingresos) / max) * 100}%` }} /></div>
                    <span className="bar-value">{money(f.ingresos)} <small className="muted">({f.pedidos})</small></span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {tab === 'vendidos' && (vista.filas.length === 0 ? <EmptyState title="No hay ventas registradas" /> : (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>#</th><th>Producto</th><th>Categoría</th><th>Unidades</th><th className="right">Ingresos</th></tr></thead>
                <tbody>
                  {vista.filas.map((f, i) => (
                    <tr key={`${f.producto_id}-${f.nombre}`}><td>{i + 1}</td><td><b>{f.nombre}</b></td><td>{f.categoria || '—'}</td><td>{f.unidades}</td><td className="right">{money(f.ingresos)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}

          {tab === 'sinventas' && (vista.productos.length === 0 ? <EmptyState title="Todos los productos tienen ventas en este periodo" /> : (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Producto</th><th>Categoría</th><th>Stock</th><th>Precio</th></tr></thead>
                <tbody>
                  {vista.productos.map((p) => <tr key={p.id}><td><b>{p.nombre}</b></td><td>{p.categoria_nombre || '—'}</td><td>{p.stock}</td><td>{money(p.precio)}</td></tr>)}
                </tbody>
              </table>
            </div>
          ))}
        </>
      )}
    </>
  )
}

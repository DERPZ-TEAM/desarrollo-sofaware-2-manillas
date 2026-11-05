import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Alert, EmptyState, Loader, Reintentar } from '../../components/ui'
import { fecha, money } from '../../utils/format'

const PESTANAS = [
  { id: 'productos', titulo: 'Productos' },
  { id: 'categorias', titulo: 'Categorías' },
  { id: 'clientes', titulo: 'Clientes' },
]

function nombreDe(tipo, x) {
  if (tipo === 'clientes') return `${x.nombres} ${x.apellidos}`.trim()
  return x.nombre
}

/**
 * Papelera: lo eliminado desde el panel (borrado LÓGICO).
 * Desde aquí se puede Restaurar o Eliminar definitivamente (borrado FÍSICO).
 */
export default function AdminPapelera() {
  const [tab, setTab] = useState('productos')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState({ type: '', text: '' })
  const [ocupado, setOcupado] = useState(null)

  const cargar = () => api('/admin/papelera/').then(setData).catch((e) => setError(e.message))
  useEffect(() => { cargar() }, [])

  async function accion(x, metodo) {
    const nombre = nombreDe(tab, x)
    if (metodo === 'DELETE') {
      const avisos = {
        productos: 'Se borrará para siempre, junto con su foto. Las ventas pasadas se conservan.',
        categorias: 'Se borrará para siempre. Sus productos quedarán "sin categoría".',
        clientes: 'Se borrará para siempre, junto con su cuenta web si tiene.',
      }
      if (!window.confirm(`¿Eliminar DEFINITIVAMENTE "${nombre}"?\n\n${avisos[tab]}\n\nEsta acción NO se puede deshacer.`)) return
    }
    setOcupado(x.id)
    try {
      const r = await api(`/admin/papelera/${tab}/${x.id}/`, { method: metodo })
      setMsg({ type: 'ok', text: r.detail })
      await cargar()
    } catch (e) {
      setMsg({ type: 'error', text: e.message })
    } finally {
      setOcupado(null)
    }
  }

  const lista = data ? data[tab] : []

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Papelera</h1>
          <p className="muted">Lo que se eliminó desde el panel. Puedes restaurarlo o eliminarlo definitivamente.</p>
        </div>
      </div>
      <Alert>{error}</Alert>
      <Alert type={msg.type} onClose={() => setMsg({ type: '', text: '' })}>{msg.text}</Alert>

      <div className="tabs">
        {PESTANAS.map((p) => (
          <button key={p.id} className={tab === p.id ? 'active' : ''} onClick={() => setTab(p.id)}>
            {p.titulo}{data && data[p.id].length > 0 ? ` (${data[p.id].length})` : ''}
          </button>
        ))}
      </div>

      {!data ? (error ? <Reintentar /> : <Loader />) : lista.length === 0 ? (
        <EmptyState title="La papelera está vacía">No hay {PESTANAS.find((p) => p.id === tab).titulo.toLowerCase()} eliminados.</EmptyState>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>{tab === 'productos' ? 'Precio' : tab === 'categorias' ? 'Productos' : 'Pedidos'}</th>
                <th>Eliminado</th>
                <th className="right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((x) => (
                <tr key={x.id}>
                  <td><b>{nombreDe(tab, x)}</b>{tab === 'clientes' && x.numero_documento && <><br /><small className="muted">{x.tipo_documento} {x.numero_documento}</small></>}</td>
                  <td>{tab === 'productos' ? money(x.precio) : tab === 'categorias' ? x.total_productos : x.total_pedidos}</td>
                  <td>{fecha(x.eliminado_en, true)}</td>
                  <td className="row-actions right">
                    <button className="btn btn-ghost btn-sm" disabled={ocupado === x.id} onClick={() => accion(x, 'POST')}>Restaurar</button>
                    <button className="btn btn-danger btn-sm" disabled={ocupado === x.id} onClick={() => accion(x, 'DELETE')}>Eliminar definitivamente</button>
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

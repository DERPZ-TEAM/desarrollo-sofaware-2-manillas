import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../api/client'
import { Alert, Field, Modal } from '../../components/ui'
import { TIPOS_DOCUMENTO, errorDocumento, money } from '../../utils/format'

const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia bancaria' },
  { value: 'nequi', label: 'Nequi / Daviplata' },
  { value: 'tarjeta', label: 'Tarjeta' },
]
// Mismos descuentos por volumen que el backend (services.DESCUENTOS_POR_VOLUMEN)
const DESCUENTOS = [[24, 15], [12, 10], [6, 5]]
const NUEVO = { nombres: '', apellidos: '', correo: '', telefono: '', ciudad: '', departamento: '' }

/**
 * Venta en el local: el administrador registra QUÉ compró un cliente en la tienda física.
 * Los productos se buscan por REFERENCIA (la de la etiqueta) o por nombre; con un lector
 * de código de barras basta escanear: el lector escribe la referencia y presiona Enter.
 * Crea (si hace falta) el cliente y su pedido en una sola operación y descuenta el stock.
 */
export default function VentaLocalModal({ open, clienteFijo, onClose, onSaved }) {
  const [doc, setDoc] = useState({ tipo: 'CC', numero: '' })
  const [encontrado, setEncontrado] = useState(null)
  const [nuevo, setNuevo] = useState(NUEVO)
  const [busqueda, setBusqueda] = useState('')
  const [resultados, setResultados] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [aviso, setAviso] = useState('')
  const [lineas, setLineas] = useState([])          // [{ producto, cantidad }]
  const [metodo, setMetodo] = useState('efectivo')
  const [notas, setNotas] = useState('')
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)
  const buscador = useRef(null)

  useEffect(() => {
    if (!open) return
    setDoc({ tipo: 'CC', numero: '' }); setEncontrado(null); setNuevo(NUEVO)
    setBusqueda(''); setResultados([]); setAviso(''); setLineas([])
    setMetodo('efectivo'); setNotas(''); setErrors({}); setError('')
  }, [open])

  // ¿El documento ya es de un cliente? (para no duplicarlo)
  useEffect(() => {
    if (!open || clienteFijo) return
    const limpio = doc.numero.replace(/[\s.-]/g, '').toUpperCase()
    setEncontrado(null)
    if (errorDocumento(doc.tipo, limpio)) return
    const t = setTimeout(() => {
      api(`/admin/clientes/?q=${encodeURIComponent(limpio)}`)
        .then((lista) => setEncontrado(lista.find((c) => c.tipo_documento === doc.tipo && c.numero_documento === limpio) || null))
        .catch(() => {})
    }, 350)
    return () => clearTimeout(t)
  }, [doc, open, clienteFijo])

  // Buscador de productos: el servidor busca y devuelve máximo 8 (sirve igual con 10 millones)
  useEffect(() => {
    const texto = busqueda.trim()
    if (!open || texto.length < 2) { setResultados([]); return }
    const t = setTimeout(() => {
      setBuscando(true)
      api(`/productos/?q=${encodeURIComponent(texto)}&activo=true&disponibles=true&limite=8`)
        .then(setResultados).catch(() => setResultados([])).finally(() => setBuscando(false))
    }, 250)
    return () => clearTimeout(t)
  }, [busqueda, open])

  function agregar(producto) {
    setLineas((ls) => {
      const ya = ls.find((l) => l.producto.id === producto.id)
      if (ya) return ls.map((l) => (l === ya ? { ...l, cantidad: Math.min(l.cantidad + 1, producto.stock) } : l))
      return [...ls, { producto, cantidad: 1 }]
    })
    setBusqueda(''); setResultados([]); setAviso('')
    setErrors((e) => ({ ...e, items: undefined }))
    buscador.current?.focus()
  }

  // Enter: si es una referencia exacta (o hay un solo resultado) se agrega directo
  async function enterEnBuscador(ev) {
    if (ev.key !== 'Enter') return
    ev.preventDefault()
    const texto = busqueda.trim()
    if (!texto) return
    try {
      const exacto = await api(`/productos/?referencia=${encodeURIComponent(texto)}&activo=true`)
      if (exacto.length) {
        if (exacto[0].stock > 0) agregar(exacto[0])
        else setAviso(`"${exacto[0].nombre}" (${exacto[0].referencia}) está agotado.`)
        return
      }
    } catch { /* si falla, seguimos con los resultados de la búsqueda */ }
    if (resultados.length === 1) agregar(resultados[0])
    else setAviso(resultados.length ? 'Hay varios resultados: elige uno de la lista.' : `No hay productos disponibles con "${texto}".`)
  }

  function cambiarCantidad(id, valor) {
    setLineas((ls) => ls.map((l) => (l.producto.id === id ? { ...l, cantidad: valor } : l)))
    setErrors((e) => ({ ...e, items: undefined }))
  }

  const cliente = clienteFijo || encontrado
  const resumen = useMemo(() => {
    let subtotal = 0
    let piezas = 0
    for (const l of lineas) {
      const n = Number(l.cantidad) || 0
      subtotal += Number(l.producto.precio) * n
      piezas += n
    }
    const pct = (DESCUENTOS.find(([min]) => piezas >= min) || [0, 0])[1]
    const descuento = Math.round(subtotal * pct) / 100
    return { subtotal, piezas, pct, descuento, total: subtotal - descuento }
  }, [lineas])

  async function guardar(ev) {
    ev.preventDefault()
    const e = {}
    if (!cliente) {
      const d = errorDocumento(doc.tipo, doc.numero)
      if (d) e.numero_documento = d
      if (nuevo.nombres.trim().length < 2) e.nombres = 'Escribe los nombres.'
      if (nuevo.telefono && !/^[0-9+\-\s()]{7,20}$/.test(nuevo.telefono)) e.telefono = 'Teléfono no válido.'
    }
    if (!lineas.length) e.items = 'Agrega al menos un producto.'
    for (const l of lineas) {
      const n = Number(l.cantidad)
      if (!(Number.isInteger(n) && n >= 1)) e.items = `La cantidad de "${l.producto.nombre}" debe ser 1 o más.`
      else if (n > l.producto.stock) e.items = `Solo quedan ${l.producto.stock} unidades de "${l.producto.nombre}".`
    }
    setErrors(e)
    if (Object.keys(e).length) return
    setGuardando(true)
    setError('')
    try {
      const body = {
        items: lineas.map((l) => ({ producto_id: l.producto.id, cantidad: Number(l.cantidad) })),
        metodo_pago: metodo,
        notas,
        ...(cliente ? { cliente_id: cliente.id }
          : { cliente: { ...nuevo, tipo_documento: doc.tipo, numero_documento: doc.numero } }),
      }
      const r = await api('/admin/ventas-local/', { method: 'POST', body })
      onSaved(r.detail)
    } catch (err) {
      setErrors(err.fields || {})
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Modal open={open} wide title="Registrar venta en el local" onClose={onClose}>
      <form onSubmit={guardar} noValidate>
        <Alert>{error}</Alert>
        <h3>1. Cliente</h3>
        {clienteFijo ? (
          <p className="hint-box"><b>{`${clienteFijo.nombres} ${clienteFijo.apellidos}`.trim()}</b>
            {clienteFijo.numero_documento ? ` · ${clienteFijo.tipo_documento} ${clienteFijo.numero_documento}` : ''}</p>
        ) : (
          <>
            <div className="two">
              <Field label="Tipo de documento">
                <select value={doc.tipo} onChange={(e) => setDoc({ ...doc, tipo: e.target.value })}>
                  {TIPOS_DOCUMENTO.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </Field>
              <Field label="Número de documento *" error={errors.numero_documento}>
                <input value={doc.numero} onChange={(e) => { setDoc({ ...doc, numero: e.target.value }); setErrors((x) => ({ ...x, numero_documento: undefined })) }} />
              </Field>
            </div>
            {encontrado ? (
              <p className="hint-box">Cliente ya registrado: <b>{`${encontrado.nombres} ${encontrado.apellidos}`.trim()}</b> ({encontrado.total_pedidos} compras). La venta se le suma a su historial.</p>
            ) : (
              <>
                <div className="two">
                  <Field label="Nombres *" error={errors.nombres}><input value={nuevo.nombres} onChange={(e) => setNuevo({ ...nuevo, nombres: e.target.value })} /></Field>
                  <Field label="Apellidos" error={errors.apellidos}><input value={nuevo.apellidos} onChange={(e) => setNuevo({ ...nuevo, apellidos: e.target.value })} /></Field>
                </div>
                <div className="two">
                  <Field label="Teléfono" error={errors.telefono}><input value={nuevo.telefono} onChange={(e) => setNuevo({ ...nuevo, telefono: e.target.value })} inputMode="tel" /></Field>
                  <Field label="Correo" error={errors.correo}><input type="email" value={nuevo.correo} onChange={(e) => setNuevo({ ...nuevo, correo: e.target.value })} /></Field>
                </div>
              </>
            )}
          </>
        )}

        <h3>2. Qué compró</h3>
        <Field label="Referencia o nombre" hint="Escribe la referencia de la etiqueta (ej. AN-18K-BL-DI-001) o escanéala y presiona Enter." error={errors.items}>
          <div className="buscador">
            <input
              ref={buscador}
              value={busqueda}
              onChange={(e) => { setBusqueda(e.target.value); setAviso('') }}
              onKeyDown={enterEnBuscador}
              placeholder="AN-18K… o anillo"
              autoComplete="off"
            />
            {(resultados.length > 0 || buscando) && (
              <ul className="buscador-resultados">
                {buscando && !resultados.length && <li className="muted">Buscando…</li>}
                {resultados.map((p) => (
                  <li key={p.id}>
                    <button type="button" onClick={() => agregar(p)}>
                      <code>{p.referencia}</code> <span>{p.nombre}</span>
                      <small>{money(p.precio)} · {p.stock} disp.</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Field>
        {aviso && <p className="field-error">{aviso}</p>}

        {lineas.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Referencia</th><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Subtotal</th><th /></tr></thead>
              <tbody>
                {lineas.map((l) => (
                  <tr key={l.producto.id}>
                    <td><code>{l.producto.referencia}</code></td>
                    <td>{l.producto.nombre}<br /><small className="muted">{l.producto.stock} disponibles</small></td>
                    <td>{money(l.producto.precio)}</td>
                    <td><input className="input-cantidad" type="number" min="1" max={l.producto.stock} value={l.cantidad} onChange={(e) => cambiarCantidad(l.producto.id, e.target.value)} /></td>
                    <td>{money(Number(l.producto.precio) * (Number(l.cantidad) || 0))}</td>
                    <td className="right"><button type="button" className="btn btn-ghost btn-sm" onClick={() => setLineas((ls) => ls.filter((x) => x !== l))}>Quitar</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <h3>3. Pago</h3>
        <div className="two">
          <Field label="Método de pago">
            <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>
              {METODOS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </Field>
          <Field label="Notas (opcional)"><input value={notas} onChange={(e) => setNotas(e.target.value)} /></Field>
        </div>
        <p>
          Subtotal: <b>{money(resumen.subtotal)}</b>
          {resumen.pct > 0 && <> · Descuento {resumen.pct}%: −{money(resumen.descuento)}</>}
          <br />Total: <b>{money(resumen.total)}</b> <small className="muted">({resumen.piezas} piezas)</small>
        </p>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancelar</button>
          <button className="btn btn-dark" disabled={guardando}>{guardando ? 'Guardando…' : 'Registrar venta'}</button>
        </div>
      </form>
    </Modal>
  )
}

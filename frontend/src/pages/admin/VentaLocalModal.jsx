import { useEffect, useMemo, useState } from 'react'
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
 * Crea (si hace falta) el cliente y su pedido en una sola operación, y descuenta el stock.
 */
export default function VentaLocalModal({ open, clienteFijo, onClose, onSaved }) {
  const [productos, setProductos] = useState([])
  const [doc, setDoc] = useState({ tipo: 'CC', numero: '' })
  const [encontrado, setEncontrado] = useState(null)
  const [nuevo, setNuevo] = useState(NUEVO)
  const [lineas, setLineas] = useState([{ producto_id: '', cantidad: 1 }])
  const [metodo, setMetodo] = useState('efectivo')
  const [notas, setNotas] = useState('')
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    if (!open) return
    setDoc({ tipo: 'CC', numero: '' }); setEncontrado(null); setNuevo(NUEVO)
    setLineas([{ producto_id: '', cantidad: 1 }]); setMetodo('efectivo'); setNotas('')
    setErrors({}); setError('')
    api('/productos/').then((r) => setProductos((r.results || r).filter((p) => p.activo && p.stock > 0))).catch((e) => setError(e.message))
  }, [open])

  // Busca si el documento ya es de un cliente (para no duplicarlo)
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

  const cliente = clienteFijo || encontrado
  const porId = useMemo(() => Object.fromEntries(productos.map((p) => [String(p.id), p])), [productos])
  const resumen = useMemo(() => {
    let subtotal = 0
    let piezas = 0
    for (const l of lineas) {
      const p = porId[String(l.producto_id)]
      if (p) { subtotal += Number(p.precio) * Number(l.cantidad || 0); piezas += Number(l.cantidad || 0) }
    }
    const pct = (DESCUENTOS.find(([min]) => piezas >= min) || [0, 0])[1]
    const descuento = Math.round(subtotal * pct) / 100
    return { subtotal, piezas, pct, descuento, total: subtotal - descuento }
  }, [lineas, porId])

  function cambiarLinea(i, campo, valor) {
    setLineas((ls) => ls.map((l, j) => (j === i ? { ...l, [campo]: valor } : l)))
    setErrors((e) => ({ ...e, items: undefined }))
  }

  async function guardar(ev) {
    ev.preventDefault()
    const e = {}
    if (!cliente) {
      const d = errorDocumento(doc.tipo, doc.numero)
      if (d) e.numero_documento = d
      if (nuevo.nombres.trim().length < 2) e.nombres = 'Escribe los nombres.'
      if (nuevo.telefono && !/^[0-9+\-\s()]{7,20}$/.test(nuevo.telefono)) e.telefono = 'Teléfono no válido.'
    }
    const items = lineas.filter((l) => l.producto_id).map((l) => ({ producto_id: Number(l.producto_id), cantidad: Number(l.cantidad) }))
    if (!items.length) e.items = 'Agrega al menos un producto.'
    for (const it of items) {
      const p = porId[String(it.producto_id)]
      if (!(it.cantidad >= 1)) e.items = 'Cada cantidad debe ser 1 o más.'
      else if (p && it.cantidad > p.stock) e.items = `Solo quedan ${p.stock} unidades de "${p.nombre}".`
    }
    setErrors(e)
    if (Object.keys(e).length) return
    setGuardando(true)
    setError('')
    try {
      const body = {
        items, metodo_pago: metodo, notas,
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
    <Modal open={open} title="Registrar venta en el local" onClose={onClose}>
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
        {lineas.map((l, i) => (
          <div className="two" key={i}>
            <Field label={i === 0 ? 'Producto' : ''}>
              <select value={l.producto_id} onChange={(e) => cambiarLinea(i, 'producto_id', e.target.value)}>
                <option value="">Selecciona…</option>
                {productos.map((p) => <option key={p.id} value={p.id}>{p.nombre} · {money(p.precio)} · {p.stock} disp.</option>)}
              </select>
            </Field>
            <Field label={i === 0 ? 'Cantidad' : ''}>
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="number" min="1" value={l.cantidad} onChange={(e) => cambiarLinea(i, 'cantidad', e.target.value)} />
                {lineas.length > 1 && <button type="button" className="btn btn-ghost btn-sm" onClick={() => setLineas((ls) => ls.filter((_, j) => j !== i))}>Quitar</button>}
              </div>
            </Field>
          </div>
        ))}
        {errors.items && <p className="field-error">{typeof errors.items === 'string' ? errors.items : 'Revisa los productos.'}</p>}
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => setLineas((ls) => [...ls, { producto_id: '', cantidad: 1 }])}>+ Otro producto</button>

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

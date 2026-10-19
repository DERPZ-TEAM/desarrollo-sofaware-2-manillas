import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { Alert, EmptyState, Field, Loader } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { money } from '../../utils/format'

const METODOS = [
  { value: 'contraentrega', label: 'Pago contra entrega', desc: 'Pagas en efectivo al recibir.' },
  { value: 'transferencia', label: 'Transferencia bancaria', desc: 'Te contactamos con los datos para pagar.' },
  { value: 'nequi', label: 'Nequi / Daviplata', desc: 'Te contactamos con el número para pagar.' },
  { value: 'tarjeta', label: 'Tarjeta (simulado)', desc: 'Demostración: no se cobra dinero real.' },
]

/** Checkout: datos de envío + método de pago + confirmación (HU-VE-019, 020, 021). */
export default function Checkout() {
  const { user, setCartCount } = useAuth()
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [form, setForm] = useState({
    nombre_destinatario: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
    telefono_contacto: user.telefono || '',
    direccion_envio: user.direccion || '',
    ciudad: user.ciudad || '',
    departamento: user.departamento || '',
    metodo_pago: '',
    notas: '',
    guardar_direccion: true,
  })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => { api('/carrito/').then(setCart).catch((e) => setError(e.message)) }, [])

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })) }

  function validar() {
    const e = {}
    if (form.nombre_destinatario.trim().length < 2) e.nombre_destinatario = 'Escribe quién recibe el pedido.'
    if (!/^[0-9+\-\s()]{7,20}$/.test(form.telefono_contacto.trim())) e.telefono_contacto = 'Teléfono no válido.'
    if (form.direccion_envio.trim().length < 6) e.direccion_envio = 'Escribe la dirección completa.'
    if (!form.ciudad.trim()) e.ciudad = 'Escribe la ciudad.'
    if (!form.departamento.trim()) e.departamento = 'Escribe el departamento.'
    if (!form.metodo_pago) e.metodo_pago = 'Selecciona un método de pago.'
    return e
  }

  async function confirmar(ev) {
    ev.preventDefault()
    const e = validar()
    setErrors(e)
    if (Object.keys(e).length) { setError('Revisa los campos marcados.'); return }
    setSending(true)
    setError('')
    try {
      const pedido = await api('/checkout/', { method: 'POST', body: form })
      setCartCount(0)
      navigate(`/pedido/${pedido.id}`, { state: { nuevo: true } })
    } catch (err) {
      setErrors(err.fields || {})
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  if (!cart) return <div className="wrap section"><Alert>{error}</Alert><Loader /></div>
  if (cart.items.length === 0) {
    return <div className="wrap section"><EmptyState title="No hay nada que pagar" action={<Link to="/catalogo" className="btn btn-dark">Ir al catálogo</Link>} /></div>
  }

  const r = cart.resumen
  return (
    <div className="wrap section">
      <div className="section-head left">
        <span className="eyebrow">Paso final</span>
        <h1>Finalizar compra</h1>
      </div>
      <form className="cart-layout" onSubmit={confirmar} noValidate>
        <div>
          <Alert>{error}</Alert>
          <div className="panel">
            <h3>1. Datos de envío</h3>
            <div className="two">
              <Field label="Nombre de quien recibe" error={errors.nombre_destinatario}>
                <input value={form.nombre_destinatario} onChange={(e) => set('nombre_destinatario', e.target.value)} />
              </Field>
              <Field label="Teléfono de contacto" error={errors.telefono_contacto}>
                <input value={form.telefono_contacto} onChange={(e) => set('telefono_contacto', e.target.value)} inputMode="tel" />
              </Field>
            </div>
            <Field label="Dirección" error={errors.direccion_envio}>
              <input value={form.direccion_envio} onChange={(e) => set('direccion_envio', e.target.value)} placeholder="Calle, número, barrio, apto" />
            </Field>
            <div className="two">
              <Field label="Ciudad" error={errors.ciudad}>
                <input value={form.ciudad} onChange={(e) => set('ciudad', e.target.value)} />
              </Field>
              <Field label="Departamento" error={errors.departamento}>
                <input value={form.departamento} onChange={(e) => set('departamento', e.target.value)} />
              </Field>
            </div>
            <Field label="Notas para la entrega (opcional)">
              <textarea rows="2" value={form.notas} onChange={(e) => set('notas', e.target.value)} />
            </Field>
            <label className="check">
              <input type="checkbox" checked={form.guardar_direccion} onChange={(e) => set('guardar_direccion', e.target.checked)} />
              Guardar esta dirección para próximas compras
            </label>
          </div>

          <div className="panel">
            <h3>2. Método de pago</h3>
            <div className="pay-options">
              {METODOS.map((m) => (
                <label key={m.value} className={`pay-option ${form.metodo_pago === m.value ? 'selected' : ''}`}>
                  <input type="radio" name="pago" value={m.value} checked={form.metodo_pago === m.value} onChange={() => set('metodo_pago', m.value)} />
                  <b>{m.label}</b>
                  <small>{m.desc}</small>
                </label>
              ))}
            </div>
            {errors.metodo_pago && <small className="field-error">{errors.metodo_pago}</small>}
          </div>
        </div>

        <aside className="summary">
          <h3>Tu pedido</h3>
          {cart.items.map((i) => (
            <div className="sum-row" key={i.id}><span>{i.cantidad} × {i.producto.nombre}</span><span>{money(i.subtotal)}</span></div>
          ))}
          <div className="sum-row"><span>Subtotal</span><span>{money(r.subtotal)}</span></div>
          {Number(r.descuento) > 0 && <div className="sum-row gold"><span>Descuento ({Number(r.porcentaje_descuento)}%)</span><span>−{money(r.descuento)}</span></div>}
          <div className="sum-row"><span>Envío</span><span>Gratis</span></div>
          <div className="sum-row total"><span>Total a pagar</span><span>{money(r.total)}</span></div>
          <button className="btn btn-gold btn-block" disabled={sending}>{sending ? 'Confirmando…' : 'Confirmar compra'}</button>
          <Link to="/carrito" className="btn btn-link btn-block">Volver al carrito</Link>
        </aside>
      </form>
    </div>
  )
}

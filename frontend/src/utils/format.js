// Funciones pequeñas de formato que se usan en muchas pantallas.

export function money(valor) {
  return Number(valor || 0).toLocaleString('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  })
}

export function fecha(valor, conHora = false) {
  if (!valor) return '—'
  return new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric',
    ...(conHora ? { hour: '2-digit', minute: '2-digit' } : {}),
  })
}

export const ESTADOS_PEDIDO = {
  pendiente: 'Pendiente',
  confirmado: 'Confirmado',
  enviado: 'Enviado',
  entregado: 'Entregado',
  cancelado: 'Cancelado',
}

export const IMAGEN_RESPALDO =
  'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><rect width="400" height="400" fill="#f3ede2"/>' +
    '<circle cx="200" cy="200" r="90" fill="none" stroke="#c9a45c" stroke-width="14"/>' +
    '<circle cx="200" cy="200" r="66" fill="none" stroke="#e7d3a8" stroke-width="4"/></svg>'
  )

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

// Tipos de documento (deben coincidir con Cliente.TIPOS_DOCUMENTO del backend)
export const TIPOS_DOCUMENTO = [
  { value: 'CC', label: 'Cédula de ciudadanía' },
  { value: 'CE', label: 'Cédula de extranjería' },
  { value: 'TI', label: 'Tarjeta de identidad' },
  { value: 'PAS', label: 'Pasaporte' },
]

/** Valida el documento en el navegador (el backend vuelve a validarlo). Devuelve '' si está bien. */
export function errorDocumento(tipo, numero) {
  const limpio = (numero || '').replace(/[\s.-]/g, '')
  if (!limpio) return 'Escribe tu número de documento.'
  const reglas = {
    CC: [/^\d{6,10}$/, 'La cédula debe tener entre 6 y 10 números.'],
    TI: [/^\d{6,11}$/, 'La tarjeta de identidad debe tener entre 6 y 11 números.'],
    CE: [/^[A-Za-z0-9]{4,12}$/, 'Entre 4 y 12 letras o números.'],
    PAS: [/^[A-Za-z0-9]{5,15}$/, 'Entre 5 y 15 letras o números.'],
  }
  const [patron, mensaje] = reglas[tipo] || reglas.CC
  return patron.test(limpio) ? '' : mensaje
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

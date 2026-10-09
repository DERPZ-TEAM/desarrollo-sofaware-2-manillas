const API = '/api'

function getToken() {
  return localStorage.getItem('gb_access')
}

export function setTokens({ access, refresh, user }) {
  localStorage.setItem('gb_access', access)
  localStorage.setItem('gb_refresh', refresh)
  localStorage.setItem('gb_user', JSON.stringify(user))
}

export function clearTokens() {
  localStorage.removeItem('gb_access')
  localStorage.removeItem('gb_refresh')
  localStorage.removeItem('gb_user')
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('gb_user') || 'null')
  } catch {
    return null
  }
}

const LABELS = {
  username: 'Usuario',
  password: 'Contraseña',
  password2: 'Confirmación',
  email: 'Correo',
  primer_nombre: 'Nombre',
  apellidos: 'Apellidos',
  telefono: 'Teléfono',
  nombre: 'Nombre',
  descripcion: 'Descripción',
  precio: 'Precio',
  stock: 'Stock',
  imagen: 'Imagen',
  non_field_errors: '',
}

export function formatError(data) {
  if (!data) return 'No se pudo completar la solicitud.'
  if (typeof data.detail === 'string') return data.detail
  const first = Object.entries(data)[0]
  if (!first) return 'Revisa los datos e inténtalo de nuevo.'
  const [key, val] = first
  const msg = Array.isArray(val) ? val[0] : val
  const label = LABELS[key]
  if (label === '') return String(msg)
  return `${label || key}: ${msg}`
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(formatError(data))
    err.status = res.status
    err.payload = data
    throw err
  }
  return data
}

export async function apiForm(path, formData, method = 'POST') {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${API}${path}`, { method, headers, body: formData })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(formatError(data))
    err.status = res.status
    err.payload = data
    throw err
  }
  return data
}

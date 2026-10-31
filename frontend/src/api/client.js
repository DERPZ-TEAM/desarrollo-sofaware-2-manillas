/**
 * Cliente HTTP: TODAS las llamadas al backend pasan por aquí.
 *
 * - Lee la URL de la API desde la variable VITE_API_URL
 *   (en Vercel: https://<tu-servicio>.onrender.com/api). En local usa '/api',
 *   que Vite redirige a http://127.0.0.1:8000 (ver vite.config.js).
 * - Agrega el token JWT en la cabecera Authorization.
 * - Si el token "access" venció (respuesta 401), pide uno nuevo con el
 *   "refresh" y repite la petición automáticamente.
 * - Convierte cualquier error en un mensaje entendible para el usuario.
 */
export const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

const KEYS = { access: 'gb_access', refresh: 'gb_refresh', user: 'gb_user' }

export const tokens = {
  get access() { return localStorage.getItem(KEYS.access) },
  get refresh() { return localStorage.getItem(KEYS.refresh) },
  save({ access, refresh, user }) {
    if (access) localStorage.setItem(KEYS.access, access)
    if (refresh) localStorage.setItem(KEYS.refresh, refresh)
    if (user) localStorage.setItem(KEYS.user, JSON.stringify(user))
  },
  clear() {
    Object.values(KEYS).forEach((k) => localStorage.removeItem(k))
  },
  storedUser() {
    try { return JSON.parse(localStorage.getItem(KEYS.user) || 'null') } catch { return null }
  },
}

// Cuando la sesión no se puede renovar, avisamos a AuthContext para cerrar sesión
let onSessionExpired = () => {}
export function setSessionExpiredHandler(fn) { onSessionExpired = fn }

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
    this.fields = data?.errors || {}
  }
}

function mensajeDeError(data, status) {
  if (data && typeof data.detail === 'string') return data.detail
  if (status === 0) return 'No hay conexión con el servidor. Revisa tu internet o intenta en un momento.'
  if (status >= 500) return 'El servidor tuvo un problema. Intenta de nuevo en unos segundos.'
  return 'No se pudo completar la solicitud.'
}

// ---------------------------------------------------------------------------
// Servidor dormido: Render (plan gratis) apaga el backend si nadie lo usa. Mientras
// despierta, el navegador ve un error de red. En vez de mostrar "sin conexión",
// avisamos al usuario y esperamos a que /salud/ responda.
// ---------------------------------------------------------------------------
const ESPERA_MAXIMA_MS = 120000
const AVISO_LENTO_MS = 5000      // si una consulta tarda más, avisamos que se está activando
const LIMITE_CONSULTA_MS = 75000 // y si pasa de aquí la cortamos para no esperar para siempre
let despertando = null

// Varias peticiones pueden necesitar el aviso a la vez: solo se oculta cuando ninguna lo usa
let avisosActivos = 0
function aviso(cambio) {
  avisosActivos += cambio
  window.dispatchEvent(new CustomEvent('gb-servidor', { detail: avisosActivos > 0 }))
}

function esperarServidor() {
  if (!despertando) {
    aviso(1)
    despertando = (async () => {
      const limite = Date.now() + ESPERA_MAXIMA_MS
      while (Date.now() < limite) {
        try {
          const r = await fetch(`${API_URL}/salud/`)
          if (r.ok) return true
        } catch { /* sigue dormido: volvemos a intentar */ }
        await new Promise((listo) => setTimeout(listo, 3000))
      }
      return false
    })().finally(() => {
      despertando = null
      aviso(-1)
    })
  }
  return despertando
}

// Solo se repite lo que no puede duplicar nada: consultas (GET) e inicios de sesión.
// Una compra NUNCA se reintenta sola, para no crear dos pedidos.
function sePuedeRepetir(method, path) {
  return method === 'GET' || path.startsWith('/auth/login') || path.startsWith('/auth/admin/login')
}

async function recuperarDeCaida(path, opciones) {
  if (!navigator.onLine) throw new ApiError(mensajeDeError(null, 0), 0, null)
  const activo = await esperarServidor()
  if (!activo) throw new ApiError(mensajeDeError(null, 0), 0, null)
  if (sePuedeRepetir(opciones.method, path)) return api(path, { ...opciones, reintentoRed: false })
  throw new ApiError('El servidor se estaba activando y ya está listo. Por favor intenta de nuevo.', 0, null)
}

// Una sola renovación a la vez aunque varias peticiones fallen juntas
let refreshing = null
async function renovarToken() {
  if (!tokens.refresh) return false
  if (!refreshing) {
    refreshing = fetch(`${API_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
      .then(async (r) => {
        if (!r.ok) return false
        tokens.save(await r.json())   // guarda el nuevo access (y refresh rotado)
        return true
      })
      .catch(() => false)
      .finally(() => { setTimeout(() => { refreshing = null }, 0) })
  }
  return refreshing
}

/**
 * api('/productos/')                                   -> GET
 * api('/carrito/', { method: 'POST', body: {...} })    -> JSON
 * api('/productos/', { method: 'POST', body: formData })-> multipart (imágenes)
 */
export async function api(path, { method = 'GET', body, auth = true, retry = true, reintentoRed = true } = {}) {
  const headers = { Accept: 'application/json' }
  const isForm = body instanceof FormData
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (auth && tokens.access) headers.Authorization = `Bearer ${tokens.access}`

  // Solo se puede cortar lo que es seguro repetir: una compra en curso nunca se interrumpe
  const repetible = sePuedeRepetir(method, path)
  const control = new AbortController()
  let avisoMostrado = false
  const relojAviso = repetible && setTimeout(() => { avisoMostrado = true; aviso(1) }, AVISO_LENTO_MS)
  const relojCorte = repetible && setTimeout(() => control.abort(), LIMITE_CONSULTA_MS)

  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
      signal: control.signal,
    })
  } catch {
    if (reintentoRed) return recuperarDeCaida(path, { method, body, auth, retry })
    throw new ApiError(mensajeDeError(null, 0), 0, null)
  } finally {
    clearTimeout(relojAviso)
    clearTimeout(relojCorte)
    if (avisoMostrado) aviso(-1)
  }

  // 502/503/504: Render todavía está arrancando el servicio
  if ([502, 503, 504].includes(res.status) && reintentoRed && sePuedeRepetir(method, path)) {
    return recuperarDeCaida(path, { method, body, auth, retry })
  }

  if (res.status === 401 && auth && retry && tokens.refresh && !path.startsWith('/auth/login')) {
    if (await renovarToken()) return api(path, { method, body, auth, retry: false, reintentoRed })
    onSessionExpired()
    throw new ApiError('Tu sesión expiró. Inicia sesión de nuevo.', 401, null)
  }

  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(mensajeDeError(data, res.status), res.status, data)
  return data
}

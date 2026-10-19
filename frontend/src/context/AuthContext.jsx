/**
 * AuthContext: guarda QUIÉN está conectado y lo comparte con toda la app.
 *
 * Cualquier componente puede hacer:  const { user, isAdmin, login, logout } = useAuth()
 *
 * También:
 *  - Lleva el contador del carrito (icono de la bolsa).
 *  - Cierra la sesión sola tras 30 minutos sin actividad (HU-SE-032).
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api, setSessionExpiredHandler, tokens } from '../api/client'

const AuthContext = createContext(null)
const INACTIVIDAD_MS = 30 * 60 * 1000

export function AuthProvider({ children }) {
  const [user, setUser] = useState(tokens.storedUser)
  const [cartCount, setCartCount] = useState(0)
  const [aviso, setAviso] = useState('')

  const isAdmin = user?.rol === 'admin'
  const isCustomer = Boolean(user) && !isAdmin

  const logout = useCallback(async (mensaje = '') => {
    const refresh = tokens.refresh
    if (refresh) {
      // Avisamos al backend para invalidar el refresh token (lista negra)
      api('/auth/logout/', { method: 'POST', body: { refresh }, retry: false }).catch(() => {})
    }
    tokens.clear()
    setUser(null)
    setCartCount(0)
    setAviso(mensaje)
  }, [])

  useEffect(() => {
    setSessionExpiredHandler(() => {
      tokens.clear()
      setUser(null)
      setAviso('Tu sesión expiró. Vuelve a iniciar sesión.')
    })
  }, [])

  // ---- Cierre automático por inactividad ----
  const timer = useRef(null)
  useEffect(() => {
    if (!user) return undefined
    const reiniciar = () => {
      clearTimeout(timer.current)
      timer.current = setTimeout(() => logout('Cerramos tu sesión por inactividad.'), INACTIVIDAD_MS)
    }
    const eventos = ['click', 'keydown', 'scroll', 'mousemove', 'touchstart']
    eventos.forEach((e) => window.addEventListener(e, reiniciar, { passive: true }))
    reiniciar()
    return () => {
      clearTimeout(timer.current)
      eventos.forEach((e) => window.removeEventListener(e, reiniciar))
    }
  }, [user, logout])

  const refreshCart = useCallback(async () => {
    if (!isCustomer) { setCartCount(0); return }
    try {
      const cart = await api('/carrito/')
      setCartCount(cart.resumen.cantidad_items || 0)
    } catch {
      setCartCount(0)
    }
  }, [isCustomer])

  useEffect(() => { refreshCart() }, [refreshCart, user?.id])

  const login = useCallback(async (username, password, admin = false) => {
    const path = admin ? '/auth/admin/login/' : '/auth/login/'
    const data = await api(path, { method: 'POST', body: { username, password }, auth: false })
    tokens.save(data)
    setUser(data.user)
    setAviso('')
    return data.user
  }, [])

  const register = useCallback(async (payload) => {
    const data = await api('/auth/registro/', { method: 'POST', body: payload, auth: false })
    tokens.save(data)
    setUser(data.user)
    setAviso(data.detail || '¡Registro exitoso! Bienvenida(o) a GoldBracelets.')
    return data
  }, [])

  const updateUser = useCallback((data) => {
    tokens.save({ user: data })
    setUser(data)
  }, [])

  const value = useMemo(() => ({
    user, isAdmin, isCustomer, login, register, logout, updateUser,
    cartCount, setCartCount, refreshCart, aviso, setAviso,
  }), [user, isAdmin, isCustomer, login, register, logout, updateUser, cartCount, refreshCart, aviso])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, clearTokens, getStoredUser, setTokens } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser)
  const [cartCount, setCartCount] = useState(0)

  const isAdmin = Boolean(user?.is_staff || user?.rol === 'admin')
  const isCustomer = Boolean(user && !isAdmin)

  async function refreshCart() {
    if (!isCustomer) {
      setCartCount(0)
      return
    }
    try {
      const cart = await api('/carrito/')
      setCartCount(cart.cantidad_items || 0)
    } catch {
      setCartCount(0)
    }
  }

  useEffect(() => {
    refreshCart()
  }, [user?.id, isCustomer])

  async function login(username, password, admin = false) {
    const path = admin ? '/auth/admin/login/' : '/auth/login/'
    const data = await api(path, { method: 'POST', body: { username, password } })
    setTokens(data)
    setUser(data.user)
    return data.user
  }

  async function register(payload) {
    const data = await api('/auth/registro/', { method: 'POST', body: payload })
    setTokens(data)
    setUser(data.user)
    return data.user
  }

  function logout() {
    clearTokens()
    setUser(null)
    setCartCount(0)
  }

  const value = useMemo(
    () => ({ user, isAdmin, isCustomer, login, register, logout, cartCount, refreshCart, setUser }),
    [user, isAdmin, isCustomer, cartCount]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}

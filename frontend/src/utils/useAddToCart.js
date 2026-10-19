import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

/**
 * Hook reutilizable para el botón "Añadir al carrito".
 * Si no hay sesión de cliente, lleva al login.
 */
export default function useAddToCart() {
  const { isCustomer, isAdmin, setCartCount } = useAuth()
  const navigate = useNavigate()
  const [addingId, setAddingId] = useState(null)
  const [mensaje, setMensaje] = useState({ type: '', text: '' })

  async function add(producto, cantidad = 1) {
    if (isAdmin) {
      setMensaje({ type: 'info', text: 'El administrador gestiona la tienda; para comprar usa una cuenta de cliente.' })
      return
    }
    if (!isCustomer) {
      navigate('/ingresar', { state: { from: `/producto/${producto.id}` } })
      return
    }
    setAddingId(producto.id)
    try {
      const carrito = await api('/carrito/', { method: 'POST', body: { producto_id: producto.id, cantidad } })
      setCartCount(carrito.resumen.cantidad_items)
      setMensaje({ type: carrito.advertencia ? 'info' : 'ok', text: carrito.detail || 'Producto agregado.' })
    } catch (e) {
      setMensaje({ type: 'error', text: e.message })
    } finally {
      setAddingId(null)
    }
  }

  return { add, addingId, mensaje, clearMensaje: () => setMensaje({ type: '', text: '' }) }
}

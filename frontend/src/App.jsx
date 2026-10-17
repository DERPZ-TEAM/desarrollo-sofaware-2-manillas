/**
 * Mapa de pantallas (rutas) del frontend.
 *
 * Dos flujos independientes:
 *   - Tienda (cliente):   /, /catalogo, /producto/:id, /carrito, /checkout, /cuenta ...
 *   - Panel (admin):      /admin/...   protegido por <RequireAdmin>
 */
import { Route, Routes } from 'react-router-dom'
import { RequireAdmin, RequireCustomer } from './components/ProtectedRoute'
import AdminLayout from './layouts/AdminLayout'
import StoreLayout from './layouts/StoreLayout'

import Home from './pages/store/Home'
import Catalog from './pages/store/Catalog'
import Product from './pages/store/Product'
import Cart from './pages/store/Cart'
import Checkout from './pages/store/Checkout'
import OrderDetail from './pages/store/OrderDetail'
import Profile from './pages/store/Profile'
import Login from './pages/store/Login'
import Register from './pages/store/Register'
import ForgotPassword from './pages/store/ForgotPassword'
import ResetPassword from './pages/store/ResetPassword'
import NotFound from './pages/store/NotFound'

import AdminLogin from './pages/admin/AdminLogin'
import Dashboard from './pages/admin/Dashboard'
import AdminProducts from './pages/admin/AdminProducts'
import AdminCategories from './pages/admin/AdminCategories'
import AdminInventory from './pages/admin/AdminInventory'
import AdminOrders from './pages/admin/AdminOrders'
import AdminClients from './pages/admin/AdminClients'
import AdminReports from './pages/admin/AdminReports'

export default function App() {
  return (
    <Routes>
      {/* ---------- Flujo del CLIENTE ---------- */}
      <Route element={<StoreLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/catalogo" element={<Catalog />} />
        <Route path="/producto/:id" element={<Product />} />
        <Route path="/carrito" element={<RequireCustomer><Cart /></RequireCustomer>} />
        <Route path="/checkout" element={<RequireCustomer><Checkout /></RequireCustomer>} />
        <Route path="/pedido/:id" element={<RequireCustomer><OrderDetail /></RequireCustomer>} />
        <Route path="/cuenta" element={<RequireCustomer><Profile /></RequireCustomer>} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="/ingresar" element={<Login />} />
      <Route path="/registro" element={<Register />} />
      <Route path="/recuperar" element={<ForgotPassword />} />
      <Route path="/restablecer/:uid/:token" element={<ResetPassword />} />

      {/* ---------- Flujo del ADMINISTRADOR ---------- */}
      <Route path="/admin/ingresar" element={<AdminLogin />} />
      <Route path="/admin" element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
        <Route index element={<Dashboard />} />
        <Route path="productos" element={<AdminProducts />} />
        <Route path="categorias" element={<AdminCategories />} />
        <Route path="inventario" element={<AdminInventory />} />
        <Route path="pedidos" element={<AdminOrders />} />
        <Route path="clientes" element={<AdminClients />} />
        <Route path="reportes" element={<AdminReports />} />
      </Route>
    </Routes>
  )
}

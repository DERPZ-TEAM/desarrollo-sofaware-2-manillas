import { Navigate, Route, Routes, Link, NavLink } from 'react-router-dom'
import { useAuth } from './AuthContext'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Cart from './pages/Cart'
import Profile from './pages/Profile'
import Product from './pages/Product'
import AdminLogin from './pages/admin/AdminLogin'
import AdminLayout from './pages/admin/AdminLayout'
import Dashboard from './pages/admin/Dashboard'
import AdminProducts from './pages/admin/AdminProducts'
import AdminCategories from './pages/admin/AdminCategories'
import AdminOrders from './pages/admin/AdminOrders'
import AdminClients from './pages/admin/AdminClients'

function StoreLayout({ children }) {
  const { user, isCustomer, cartCount, logout } = useAuth()
  return (
    <>
      <div className="topbar">Compra segura · Envíos a todo el país · Piezas con alma en oro</div>
      <nav className="nav">
        <Link to="/" className="brand">GOLDBRACELETS<small>JOYERÍA</small></Link>
        <div className="nav-links">
          <NavLink to="/" end>Inicio</NavLink>
          <a href="/#catalogo">Catálogo</a>
          <NavLink to="/cuenta">Contacto</NavLink>
        </div>
        <div className="nav-actions">
          {isCustomer ? (
            <>
              <Link to="/cuenta" className="icon-btn" title="Mi cuenta">👤</Link>
              <Link to="/carrito" className="icon-btn" title="Carrito">
                👜
                {cartCount > 0 && <span className="badge">{cartCount}</span>}
              </Link>
              <button className="btn btn-ghost btn-sm" onClick={logout}>Salir</button>
            </>
          ) : user?.is_staff ? (
            <Link className="btn btn-dark btn-sm" to="/admin">Panel</Link>
          ) : (
            <>
              <Link to="/ingresar">Ingresar</Link>
              <Link className="btn btn-dark btn-sm" to="/registro">Crear cuenta</Link>
            </>
          )}
        </div>
      </nav>
      {children}
      <footer className="footer">GoldBracelets · La belleza de tu esencia en cada detalle</footer>
    </>
  )
}

function PrivateCustomer({ children }) {
  const { isCustomer, user } = useAuth()
  if (!user) return <Navigate to="/ingresar" replace />
  if (!isCustomer) return <Navigate to="/admin" replace />
  return children
}

function PrivateAdmin({ children }) {
  const { isAdmin, user } = useAuth()
  if (!user) return <Navigate to="/admin/ingresar" replace />
  if (!isAdmin) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<StoreLayout><Home /></StoreLayout>} />
      <Route path="/producto/:id" element={<StoreLayout><Product /></StoreLayout>} />
      <Route path="/ingresar" element={<Login />} />
      <Route path="/registro" element={<Register />} />
      <Route path="/carrito" element={<StoreLayout><PrivateCustomer><Cart /></PrivateCustomer></StoreLayout>} />
      <Route path="/cuenta" element={<StoreLayout><PrivateCustomer><Profile /></PrivateCustomer></StoreLayout>} />
      <Route path="/admin/ingresar" element={<AdminLogin />} />
      <Route
        path="/admin"
        element={<PrivateAdmin><AdminLayout /></PrivateAdmin>}
      >
        <Route index element={<Dashboard />} />
        <Route path="productos" element={<AdminProducts />} />
        <Route path="categorias" element={<AdminCategories />} />
        <Route path="pedidos" element={<AdminOrders />} />
        <Route path="clientes" element={<AdminClients />} />
      </Route>
    </Routes>
  )
}

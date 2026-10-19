import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Alert } from '../components/ui'
import { useAuth } from '../context/AuthContext'

/** Estructura de la tienda: barra superior, menú, contenido y pie de página. */
export default function StoreLayout() {
  const { user, isCustomer, isAdmin, cartCount, logout, aviso, setAviso } = useAuth()
  const [menu, setMenu] = useState(false)
  const navigate = useNavigate()

  async function salir() {
    await logout()
    navigate('/')
  }

  return (
    <div className="store">
      <div className="topbar">Envíos a toda Colombia · Descuentos por mayor desde 6 piezas · Compra segura</div>
      <header className="nav">
        <Link to="/" className="brand" onClick={() => setMenu(false)}>
          <span className="brand-mark">GB</span>
          <span>GOLD<b>BRACELETS</b><small>Joyería en oro</small></span>
        </Link>
        <button className="nav-toggle" onClick={() => setMenu(!menu)} aria-label="Abrir menú">☰</button>
        <nav className={`nav-links ${menu ? 'open' : ''}`} onClick={() => setMenu(false)}>
          <NavLink to="/" end>Inicio</NavLink>
          <NavLink to="/catalogo">Catálogo</NavLink>
          {isCustomer && <NavLink to="/cuenta">Mi cuenta</NavLink>}
          {isAdmin && <NavLink to="/admin">Panel admin</NavLink>}
        </nav>
        <div className="nav-actions">
          {isCustomer && (
            <Link to="/carrito" className="cart-link" aria-label="Carrito">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6">
                <path d="M6 7h12l-1 13H7L6 7Z" /><path d="M9 7a3 3 0 0 1 6 0" />
              </svg>
              {cartCount > 0 && <span className="cart-count">{cartCount}</span>}
            </Link>
          )}
          {user ? (
            <div className="user-chip">
              <span className="avatar">{(user.first_name || user.username)[0].toUpperCase()}</span>
              <button className="btn btn-link" onClick={salir}>Salir</button>
            </div>
          ) : (
            <>
              <Link to="/ingresar" className="btn btn-link">Ingresar</Link>
              <Link to="/registro" className="btn btn-dark btn-sm">Crear cuenta</Link>
            </>
          )}
        </div>
      </header>

      {aviso && <div className="wrap" style={{ paddingTop: 16 }}><Alert type={/exitoso|bienvenid/i.test(aviso) ? 'ok' : 'info'} onClose={() => setAviso('')}>{aviso}</Alert></div>}

      <main className="store-main"><Outlet /></main>

      <footer className="footer">
        <div className="wrap footer-grid">
          <div>
            <div className="brand brand-light"><span className="brand-mark">GB</span><span>GOLD<b>BRACELETS</b></span></div>
            <p>La belleza de tu esencia en cada detalle. Piezas tejidas a mano y joyería en oro.</p>
          </div>
          <div>
            <h4>Tienda</h4>
            <Link to="/catalogo">Catálogo</Link>
            <Link to="/carrito">Carrito</Link>
            <Link to="/cuenta">Mis pedidos</Link>
          </div>
          <div>
            <h4>Ayuda</h4>
            <span>Envíos nacionales 2 a 5 días</span>
            <span>Pago contra entrega</span>
            <Link to="/admin/ingresar">Acceso administrador</Link>
          </div>
        </div>
        <p className="footer-copy">© {new Date().getFullYear()} GoldBracelets · Proyecto Desarrollo de Software II · Univalle</p>
      </footer>
    </div>
  )
}

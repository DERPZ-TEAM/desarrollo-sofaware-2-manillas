import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const LINKS = [
  { to: '/admin', label: 'Escritorio', icon: '◈', end: true },
  { to: '/admin/productos', label: 'Productos', icon: '◇' },
  { to: '/admin/categorias', label: 'Categorías', icon: '▤' },
  { to: '/admin/inventario', label: 'Inventario', icon: '▦' },
  { to: '/admin/pedidos', label: 'Pedidos', icon: '◎' },
  { to: '/admin/clientes', label: 'Clientes', icon: '◉' },
  { to: '/admin/reportes', label: 'Reportes', icon: '▲' },
]

/** Estructura del panel de administración: menú lateral oscuro + contenido. */
export default function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  async function salir() {
    await logout()
    navigate('/admin/ingresar')
  }

  return (
    <div className="admin-shell">
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <span className="brand-mark">GB</span>
          <div>GOLDBRACELETS<small>Panel de gestión</small></div>
        </div>
        <nav onClick={() => setOpen(false)}>
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              <span className="side-icon">{l.icon}</span>{l.label}
            </NavLink>
          ))}
        </nav>
        <a className="sidebar-store" href="/" target="_blank" rel="noreferrer">Ver tienda ↗</a>
      </aside>
      <div className="admin-main">
        <header className="admin-top">
          <button className="nav-toggle admin-toggle" onClick={() => setOpen(!open)} aria-label="Menú">☰</button>
          <span className="admin-title">Administración</span>
          <div className="admin-user">
            <span className="avatar">{(user?.first_name || user?.username || 'A')[0].toUpperCase()}</span>
            <span className="hide-sm">{user?.first_name || user?.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={salir}>Cerrar sesión</button>
          </div>
        </header>
        <main className="admin-content"><Outlet /></main>
      </div>
    </div>
  )
}

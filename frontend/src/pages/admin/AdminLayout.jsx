import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../AuthContext'

export default function AdminLayout() {
  const { user, logout } = useAuth()
  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <h2>GOLDBRACELETS</h2>
        <NavLink to="/admin" end>Escritorio</NavLink>
        <NavLink to="/admin/productos">Productos</NavLink>
        <NavLink to="/admin/categorias">Categorías</NavLink>
        <NavLink to="/admin/pedidos">Pedidos</NavLink>
        <NavLink to="/admin/clientes">Clientes</NavLink>
        <a href="/" target="_blank" rel="noreferrer">Ver tienda</a>
      </aside>
      <div className="admin-main">
        <header className="admin-top">
          <strong>Panel de administración</strong>
          <div>
            Hola, {user?.username} {' '}
            <button className="btn btn-ghost btn-sm" onClick={logout}>Cerrar sesión</button>
          </div>
        </header>
        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

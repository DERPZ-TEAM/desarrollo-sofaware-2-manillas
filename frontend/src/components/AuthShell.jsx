import { Link } from 'react-router-dom'

/** Marco visual compartido por login, registro y recuperación (panel negro + formulario). */
export default function AuthShell({ title, subtitle, side, children, admin = false }) {
  return (
    <div className={`auth-page ${admin ? 'auth-admin' : ''}`}>
      <div className="auth-visual">
        <Link to="/" className="brand brand-light"><span className="brand-mark">GB</span><span>GOLD<b>BRACELETS</b></span></Link>
        <div>
          <h2>{side?.title}</h2>
          <p>{side?.text}</p>
        </div>
        <div className="auth-rings" aria-hidden="true"><div className="ring ring-1" /><div className="ring ring-2" /></div>
      </div>
      <div className="auth-panel">
        <div className="auth-form">
          <h1>{title}</h1>
          {subtitle && <p className="muted">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  )
}

/**
 * Piezas pequeñas de interfaz que se reutilizan en toda la app.
 */
import { useEffect } from 'react'

export function Alert({ type = 'error', children, onClose }) {
  if (!children) return null
  return (
    <div className={`alert alert-${type}`} role={type === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
      {onClose && <button type="button" className="alert-close" onClick={onClose} aria-label="Cerrar">×</button>}
    </div>
  )
}

export function Loader({ text = 'Cargando...' }) {
  return (
    <div className="loader" role="status">
      <span className="loader-ring" />
      <span>{text}</span>
    </div>
  )
}

/** Se muestra en lugar del círculo de carga cuando la consulta ya falló. */
export function Reintentar() {
  return (
    <div className="center">
      <button type="button" className="btn btn-dark" onClick={() => window.location.reload()}>Reintentar</button>
    </div>
  )
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">◇</div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  )
}

/** Campo de formulario con etiqueta y mensaje de error debajo. */
export function Field({ label, error, hint, children, className = '' }) {
  return (
    <label className={`field ${error ? 'has-error' : ''} ${className}`}>
      <span className="field-label">{label}</span>
      {children}
      {error ? <small className="field-error">{Array.isArray(error) ? error[0] : error}</small>
        : hint ? <small className="field-hint">{hint}</small> : null}
    </label>
  )
}

export function Modal({ open, title, onClose, children, wide = false }) {
  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true"
        onMouseDown={(e) => e.stopPropagation()}>
        <header className="modal-head">
          <h3>{title}</h3>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Cerrar">×</button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function StatusBadge({ estado, children }) {
  return <span className={`badge badge-${estado}`}>{children || estado}</span>
}

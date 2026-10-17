import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/ui'

export default function NotFound() {
  return (
    <div className="wrap section">
      <EmptyState title="Página no encontrada" action={<Link to="/" className="btn btn-dark">Volver al inicio</Link>}>
        La dirección que buscas no existe.
      </EmptyState>
    </div>
  )
}

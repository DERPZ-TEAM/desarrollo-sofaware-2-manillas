import { useEffect, useState } from 'react'

/** Aviso flotante mientras el servidor se activa (plan gratis de Render). */
export default function AvisoServidor() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const escuchar = (e) => setVisible(e.detail)
    window.addEventListener('gb-servidor', escuchar)
    return () => window.removeEventListener('gb-servidor', escuchar)
  }, [])

  if (!visible) return null
  return (
    <div className="aviso-servidor" role="status">
      <span className="loader-ring" />
      <span>Estamos activando el servidor. Puede tardar hasta un minuto; la página cargará sola.</span>
    </div>
  )
}

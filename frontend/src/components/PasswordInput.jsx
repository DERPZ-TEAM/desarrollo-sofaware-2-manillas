import { useState } from 'react'

/**
 * Campo de contraseña con "ojito" que funciona como sensor:
 *  - Con mouse:   la contraseña se ve mientras el puntero está SOBRE el ojito.
 *  - Con el dedo: se ve mientras se MANTIENE presionado el ojito.
 *  - Con teclado: se ve mientras se mantiene Espacio o Enter con el ojito enfocado.
 * En cuanto se retira el mouse, el dedo o la tecla, se vuelve a ocultar.
 */
export default function PasswordInput({ value, onChange, autoComplete = 'current-password', ...props }) {
  const [visible, setVisible] = useState(false)
  const mostrar = () => setVisible(true)
  const ocultar = () => setVisible(false)

  return (
    <div className="password-field">
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
      />
      <button
        type="button"
        className={`password-eye ${visible ? 'is-visible' : ''}`}
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        aria-pressed={visible}
        title="Pasa el mouse o mantén presionado para ver la contraseña"
        // Mouse: mientras está encima
        onPointerEnter={(e) => { if (e.pointerType === 'mouse') mostrar() }}
        onPointerLeave={ocultar}
        // Dedo o lápiz: mientras se mantiene presionado
        onPointerDown={(e) => { if (e.pointerType !== 'mouse') { e.preventDefault(); mostrar() } }}
        onPointerUp={(e) => { if (e.pointerType !== 'mouse') ocultar() }}
        onPointerCancel={ocultar}
        onContextMenu={(e) => e.preventDefault()}   // evita el menú al mantener presionado en celular
        // Teclado: mientras se mantiene Espacio o Enter
        onKeyDown={(e) => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); mostrar() } }}
        onKeyUp={ocultar}
        onBlur={ocultar}
        onClick={(e) => e.preventDefault()}         // no envía el formulario
      >
        {visible ? (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path d="M3 3l18 18" />
            <path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6 0 10 7 10 7a17.6 17.6 0 0 1-3.2 3.9M6.6 6.6C3.8 8.5 2 12 2 12s4 7 10 7a9.6 9.6 0 0 0 4.4-1.1" />
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
            <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </div>
  )
}

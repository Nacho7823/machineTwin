import { useState, type KeyboardEvent } from 'react'
import type { MessageInputProps } from '../types'

export function MessageInput({ onSend, onClear, disabled }: MessageInputProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    const text = input.trim()
    if (!text || disabled) return
    setInput('')
    onSend(text)
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-input-area">
      <button
        className="clear-btn"
        onClick={onClear}
        title="Limpiar chat"
        aria-label="Limpiar chat"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 6h18"/>
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
          <line x1="10" y1="11" x2="10" y2="17"/>
          <line x1="14" y1="11" x2="14" y2="17"/>
        </svg>
      </button>
      <div className="input-wrapper">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Esperando respuesta...' : 'Escribi tu mensaje...'}
          aria-label="Mensaje"
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          aria-label="Enviar mensaje"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

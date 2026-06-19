import type { MessageListProps } from '../types'
import { MarkdownRenderer } from './MarkdownRenderer'

export function MessageList({ messages, thinking, messagesEndRef }: MessageListProps) {
  return (
    <div className="chat-messages">
      {messages.length === 0 && (
        <div className="welcome-message">
          <h2>MachineTwin</h2>
          <p>Tu asistente tecnico para maquinas.<br/>Escribi tu pregunta para empezar.</p>
        </div>
      )}

      {messages.map((msg, i) => (
        <div key={i} className={`message ${msg.role}`}>
          <div className="message-label">
            {msg.role === 'user' ? 'Vos' : <span className="message-bot-label">MachineTwin</span>}
          </div>
          <div className="message-bubble">
            {msg.role === 'bot'
              ? <MarkdownRenderer content={msg.text} />
              : msg.text
            }
          </div>
        </div>
      ))}

      {thinking && (
        <div className="thinking-indicator">
          <span />
          <span />
          <span />
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

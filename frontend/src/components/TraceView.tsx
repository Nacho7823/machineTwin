import { useCallback, useEffect, useState } from 'react'
import type { ConversationTrace, PersistedConversation, TraceEvent, TraceViewProps } from '../types'

function shortJson(value: unknown): string {
  if (value === undefined || value === null || value === '') return ''
  if (typeof value === 'string') return value.length > 320 ? `${value.slice(0, 320)}...` : value
  try {
    const text = JSON.stringify(value, null, 2)
    return text.length > 320 ? `${text.slice(0, 320)}...` : text
  } catch {
    return String(value)
  }
}

function formatDate(value?: string): string {
  if (!value) return 'sin fecha'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

function traceTitle(trace: TraceEvent): string {
  if (trace.event === 'tool_call' && trace.tool) return `Tool: ${trace.tool}`
  if (trace.event === 'rag_retrieval') return 'RAG: chunks recuperados'
  return trace.event || 'evento'
}

function dateValue(value?: string): number {
  if (!value) return 0
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 0 : date.getTime()
}

function eventTime(trace: TraceEvent): number {
  return dateValue(trace.timestamp)
}

export function TraceView({ activeConversationId }: TraceViewProps) {
  const [conversations, setConversations] = useState<PersistedConversation[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(activeConversationId)
  const [detail, setDetail] = useState<ConversationTrace | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadConversations = useCallback(async () => {
    const res = await fetch('/api/conversations')
    const data = await res.json()
    const rows: PersistedConversation[] = data.conversations || []
    setConversations(rows)
    if (!selectedId && rows[0]) {
      setSelectedId(rows[0].conversation_id)
    }
  }, [selectedId])

  useEffect(() => {
    loadConversations().catch(() => setError('No se pudieron cargar las conversaciones.'))
  }, [loadConversations])

  useEffect(() => {
    if (activeConversationId) {
      setSelectedId(activeConversationId)
    }
  }, [activeConversationId])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      return
    }
    setLoading(true)
    setError('')
    fetch(`/api/traces/${encodeURIComponent(selectedId)}`)
      .then(res => res.json())
      .then((data: ConversationTrace) => setDetail(data))
      .catch(() => setError('No se pudieron cargar las trazas.'))
      .finally(() => setLoading(false))
  }, [selectedId])

  return (
    <main className="trace-view">
      <section className="trace-sidebar" aria-label="Conversaciones persistidas">
        <div className="trace-section-header">
          <h2>Conversaciones</h2>
          <button type="button" onClick={() => loadConversations()} className="trace-refresh-btn">
            Actualizar
          </button>
        </div>
        {conversations.length === 0 && (
          <p className="trace-empty">No hay conversaciones persistidas.</p>
        )}
        <div className="trace-conversation-list">
          {conversations.map(conversation => (
            <button
              key={conversation.conversation_id}
              type="button"
              className={`trace-conversation ${conversation.conversation_id === selectedId ? 'trace-conversation--active' : ''}`}
              onClick={() => setSelectedId(conversation.conversation_id)}
            >
              <span>{conversation.title || conversation.conversation_id}</span>
              <small>{conversation.message_count} mensajes - {formatDate(conversation.updated_at)}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="trace-detail" aria-label="Detalle de trazas">
        <div className="trace-section-header">
          <h2>Trazas</h2>
          {selectedId && <span className="trace-id">{selectedId}</span>}
        </div>
        {error && <p className="trace-error">{error}</p>}
        {loading && <p className="trace-empty">Cargando trazas...</p>}
        {!loading && !detail && <p className="trace-empty">Selecciona una conversación.</p>}
        {detail && (
          <div className="trace-columns">
            <div className="trace-panel">
              <h3>Mensajes</h3>
              {detail.messages.length === 0 && <p className="trace-empty">Sin mensajes persistidos.</p>}
              {[...detail.messages].sort((a, b) => dateValue(a.created_at) - dateValue(b.created_at)).map((message, index) => (
                <article key={`${message.created_at}-${index}`} className="trace-card">
                  <strong>{message.role === 'assistant' ? 'MachineTwin' : 'Usuario'}</strong>
                  <time>{formatDate(message.created_at)}</time>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>
            <div className="trace-panel">
              <h3>Eventos y tools</h3>
              {detail.traces.length === 0 && <p className="trace-empty">Sin trazas registradas.</p>}
              {[...detail.traces].sort((a, b) => eventTime(a) - eventTime(b)).map((trace, index) => (
                <article key={`${trace.trace_id}-${trace.event}-${index}`} className="trace-card trace-event-card">
                  <strong>{traceTitle(trace)}</strong>
                  <time>{formatDate(trace.timestamp)}</time>
                  <div className="trace-meta-row">
                    {trace.step !== undefined && <span className="trace-chip">step {trace.step}</span>}
                    {trace.finish_status && <span className="trace-chip">{trace.finish_status}</span>}
                    {trace.tool_status && <span className="trace-chip">{trace.tool_status}</span>}
                    {trace.latency_ms !== undefined && <span className="trace-chip">{trace.latency_ms} ms LLM</span>}
                    {trace.tool_latency_ms !== undefined && <span className="trace-chip">{trace.tool_latency_ms} ms tool</span>}
                  </div>
                  {(trace.llm_model || trace['System Prompt version'] || trace.prompt_hash) && (
                    <dl className="trace-metadata">
                      {trace.llm_model && (
                        <>
                          <dt>Modelo</dt>
                          <dd>{trace.llm_model}</dd>
                        </>
                      )}
                      {trace['System Prompt version'] && (
                        <>
                          <dt>Prompt</dt>
                          <dd>{trace['System Prompt version']}</dd>
                        </>
                      )}
                      {trace.prompt_hash && (
                        <>
                          <dt>Hash</dt>
                          <dd>{trace.prompt_hash}</dd>
                        </>
                      )}
                    </dl>
                  )}
                  {trace.rag_chunks && trace.rag_chunks.length > 0 && (
                    <div className="trace-rag">
                      <span>{trace.rag_chunk_count || trace.rag_chunks.length} chunks recuperados</span>
                      {trace.rag_chunks.map((chunk, chunkIndex) => (
                        <div key={`${chunk.doc_id}-${chunk.chunk_index}-${chunkIndex}`} className="trace-rag-item">
                          <strong>{chunk.title || chunk.doc_id || 'documento'}</strong>
                          <small>chunk {chunk.chunk_index ?? '-'}{chunk.distance !== undefined ? ` · distancia ${chunk.distance.toFixed(4)}` : ''}</small>
                          {chunk.preview && <p>{chunk.preview}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                  {shortJson(trace.input) && <pre>{shortJson(trace.input)}</pre>}
                  {shortJson(trace.output) && <pre>{shortJson(trace.output)}</pre>}
                  {!trace.input && !trace.output && shortJson(trace.response) && <pre>{shortJson(trace.response)}</pre>}
                </article>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

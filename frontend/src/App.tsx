import { useState, useRef, useEffect, useCallback } from 'react'
import { MessageList } from './components/MessageList'
import { MessageInput } from './components/MessageInput'
import { Sidebar } from './components/Sidebar'
import { TraceView } from './components/TraceView'
import type { Message, Conversation, CompletionResponse, QuickAction, AppView, PersistedConversation, ConversationTrace } from './types'
import './App.css'

const STORAGE_KEY = 'machinetwin_conversations'

const CMD_MAP: Record<string, string> = {
  '/status': 'Dame el estado actual de las maquinas.',
  '/summary': 'Dame un resumen general de las maquinas con tendencias y anomalias.',
  '/anomalies': 'Detecta anomalias en las variables de las maquinas en las ultimas 24 horas.',
  '/events': 'Muestra los eventos recientes de las maquinas de los ultimos 7 dias.',
  '/recomend': 'Dame recomendaciones de operacion y mantenimiento.',
  '/vars': 'Analiza las tendencias de las variables principales de las maquinas usando 50 muestras recientes.',
}

const HELP_MSG = `Comandos:
  /status      Estado actual
  /summary     Resumen general
  /anomalies   Anomalias (24h)
  /events      Eventos (7 dias)
  /recomend    Recomendaciones
  /vars        Tendencias variables
  /clear       Limpiar chat`

const QUICK_ACTIONS: QuickAction[] = [
  {
    label: 'Ver alertas',
    prompt: 'Mostrame el detalle de las alertas registradas, incluyendo fecha, variable afectada, severidad y si requieren acción.',
  },
  {
    label: 'Revisar anomalías',
    prompt: 'Revisá si hay anomalías o variables fuera de la normalidad en la operación actual.',
  },
  {
    label: 'Analizar tendencias',
    prompt: 'Analizá las tendencias recientes de las variables relacionadas con las alertas o desviaciones detectadas usando 50 muestras.',
  },
  {
    label: 'Qué revisar',
    prompt: 'Indicame qué componentes o condiciones operativas debería revisar primero según las alertas y datos actuales.',
  },
]

const QUICK_ACTION_TRIGGERS = [
  'alerta',
  'alertas',
  'anomalia',
  'anomalía',
  'fuera de rango',
  'desviacion',
  'desviación',
  'revisar',
]

function shouldShowQuickActions(message?: Message): boolean {
  if (!message || message.role !== 'bot') return false
  const text = message.text.toLocaleLowerCase('es')
  return QUICK_ACTION_TRIGGERS.some(trigger => text.includes(trigger))
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function getTitleFromMessages(messages: Message[]): string {
  const firstUser = messages.find(m => m.role === 'user')
  if (firstUser) {
    return firstUser.text.slice(0, 40) + (firstUser.text.length > 40 ? '...' : '')
  }
  return 'Nueva conversacion'
}

function loadConversations(): Conversation[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

function saveConversations(conversations: Conversation[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
}

function persistedToConversation(conversation: PersistedConversation): Conversation {
  return {
    id: conversation.conversation_id,
    title: conversation.title || conversation.conversation_id,
    messages: [],
    createdAt: Date.parse(conversation.created_at) || Date.now(),
    updatedAt: Date.parse(conversation.updated_at) || Date.now(),
  }
}

function persistedMessagesToChat(detail: ConversationTrace): Message[] {
  return detail.messages.map(message => ({
    role: message.role === 'assistant' ? 'bot' : 'user',
    text: message.content,
  }))
}

function getInitialDarkMode(): boolean {
  const saved = localStorage.getItem('darkMode')
  if (saved !== null) return saved === 'true'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [pendingIds, setPendingIds] = useState<string[]>([])
  const [darkMode, setDarkMode] = useState(getInitialDarkMode)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [view, setView] = useState<AppView>('chat')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeConversation = conversations.find(c => c.id === activeId)
  const messages = activeConversation?.messages ?? []
  const thinking = activeId ? pendingIds.includes(activeId) : false
  const quickActions = shouldShowQuickActions(messages[messages.length - 1]) ? QUICK_ACTIONS : []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', String(darkMode))
  }, [darkMode])

  useEffect(() => {
    saveConversations(conversations)
  }, [conversations])

  useEffect(() => {
    fetch('/api/conversations')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then((data: { conversations?: PersistedConversation[] }) => {
        const persisted = data.conversations || []
        if (persisted.length === 0) return
        setConversations(prev => {
          const byId = new Map(prev.map(conversation => [conversation.id, conversation]))
          const merged = persisted.map(conversation => {
            const existing = byId.get(conversation.conversation_id)
            return {
              ...persistedToConversation(conversation),
              messages: existing?.messages || [],
            }
          })
          return merged
        })
        setActiveId(current => current || persisted[0]?.conversation_id || null)
      })
      .catch(() => {
        // Si el backend no esta disponible, se usa localStorage como fallback.
      })
  }, [])

  const updateConversation = useCallback((id: string, msgs: Message[]) => {
    setConversations(prev => prev.map(c =>
      c.id === id
        ? { ...c, messages: msgs, title: getTitleFromMessages(msgs), updatedAt: Date.now() }
        : c
    ))
  }, [])

  const createConversation = useCallback((initialMessages: Message[] = [], title?: string) => {
    const id = generateId()
    const newConv: Conversation = {
      id,
      title: title || getTitleFromMessages(initialMessages),
      messages: initialMessages,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    setConversations(prev => [newConv, ...prev])
    setActiveId(id)
    fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: id, title: newConv.title }),
    }).catch(() => {
      // El chat local puede seguir funcionando aunque la persistencia falle.
    })
    return id
  }, [])

  const handleNewConversation = () => {
    createConversation()
    setMobileSidebarOpen(false)
  }

  const loadPersistedConversation = useCallback(async (id: string) => {
    const res = await fetch(`/api/conversations/${encodeURIComponent(id)}`)
    if (!res.ok) throw new Error('No se pudo cargar la conversacion')
    const detail: ConversationTrace = await res.json()
    const persistedMessages = persistedMessagesToChat(detail)
    if (persistedMessages.length > 0) {
      updateConversation(id, persistedMessages)
    }
  }, [updateConversation])

  const handleSelectConversation = (id: string) => {
    const conv = conversations.find(c => c.id === id)
    if (conv) {
      setActiveId(id)
      loadPersistedConversation(id).catch(() => {
        // Se conserva la copia local si el backend no responde.
      })
    }
    setMobileSidebarOpen(false)
  }

  const handleDeleteConversation = (id: string) => {
    const remaining = conversations.filter(c => c.id !== id)
    setConversations(remaining)
    setPendingIds(prev => prev.filter(pendingId => pendingId !== id))
    if (activeId === id) {
      const nextId = remaining[0]?.id ?? null
      setActiveId(nextId)
    }
    fetch(`/api/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }).catch(() => {
      // Si falla el backend, al menos se elimina de la vista local.
    })
  }

  const clearChat = useCallback(async () => {
    if (activeId) {
      updateConversation(activeId, [])
    }

    try {
      await fetch('/api/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: activeId }),
      })
    } catch {
      // El chat visual se limpia aunque el backend no este disponible.
    }
  }, [activeId, updateConversation])

  const toggleSidebar = () => {
    if (window.matchMedia('(max-width: 768px)').matches) {
      setMobileSidebarOpen(prev => !prev)
      return
    }
    setSidebarCollapsed(prev => !prev)
  }

  const sendMessage = async (text: string) => {
    if (!text.trim()) return

    if (text === '/clear') {
      await clearChat()
      return
    }

    let currentId = activeId
    let baseMessages = messages

    if (text === '/help') {
      if (!currentId) {
        currentId = createConversation([], 'Ayuda')
        baseMessages = []
      }
      const newMsgs = [...baseMessages, { role: 'bot' as const, text: HELP_MSG }]
      updateConversation(currentId, newMsgs)
      return
    }

    if (!currentId) {
      currentId = createConversation()
      baseMessages = []
    }

    if (pendingIds.includes(currentId)) return

    const userMsg: Message = { role: 'user', text }
    const withUser = [...baseMessages, userMsg]
    updateConversation(currentId, withUser)

    setPendingIds(prev => prev.includes(currentId) ? prev : [...prev, currentId])
    const cmd = CMD_MAP[text]
    const params = new URLSearchParams({
      msg: cmd || text,
      conversation_id: currentId,
    })

    try {
      const res = await fetch(`/api/completion?${params.toString()}`)
      const data: CompletionResponse = await res.json()
      const botMsg: Message = { role: 'bot', text: data.completion }
      updateConversation(currentId, [...withUser, botMsg])
      fetch('/api/conversations')
        .then(res => res.ok ? res.json() : Promise.reject())
        .then((listData: { conversations?: PersistedConversation[] }) => {
          const persisted = listData.conversations || []
          if (persisted.length === 0) return
          setConversations(prev => {
            const byId = new Map(prev.map(conversation => [conversation.id, conversation]))
            return persisted.map(conversation => {
              const existing = byId.get(conversation.conversation_id)
              return {
                ...persistedToConversation(conversation),
                messages: existing?.messages || [],
              }
            })
          })
        })
        .catch(() => {})
    } catch {
      const errorMsg: Message = { role: 'bot', text: 'Error al conectar con el servidor.' }
      updateConversation(currentId, [...withUser, errorMsg])
    } finally {
      setPendingIds(prev => prev.filter(id => id !== currentId))
    }
  }

  return (
    <div className={`app-layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
        open={mobileSidebarOpen}
        collapsed={sidebarCollapsed}
        onClose={() => setMobileSidebarOpen(false)}
      />
      <div className="chat-container">
        <header className="chat-header">
          <button
            className="menu-btn"
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? 'Expandir historial' : 'Contraer historial'}
            aria-expanded={!sidebarCollapsed}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <h1>MachineTwin</h1>
          <div className="header-spacer" />
          <div className="view-tabs" role="tablist" aria-label="Vistas">
            <button
              type="button"
              className={view === 'chat' ? 'view-tab view-tab--active' : 'view-tab'}
              onClick={() => setView('chat')}
            >
              Chat
            </button>
            <button
              type="button"
              className={view === 'traces' ? 'view-tab view-tab--active' : 'view-tab'}
              onClick={() => setView('traces')}
            >
              Trazas
            </button>
          </div>
          <button
            className="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
            aria-label={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          >
            {darkMode ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
        </header>

        {view === 'chat' ? (
          <>
            <MessageList
              messages={messages}
              thinking={thinking}
              messagesEndRef={messagesEndRef}
              quickActions={quickActions}
              onQuickPrompt={sendMessage}
            />

            <MessageInput onSend={sendMessage} onClear={clearChat} disabled={thinking} />
          </>
        ) : (
          <TraceView activeConversationId={activeId} />
        )}
      </div>
    </div>
  )
}

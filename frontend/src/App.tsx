import { useState, useRef, useEffect, useCallback } from 'react'
import { MessageList } from './components/MessageList'
import { MessageInput } from './components/MessageInput'
import { Sidebar } from './components/Sidebar'
import type { Message, Conversation, CompletionResponse } from './types'
import './App.css'

const STORAGE_KEY = 'machinetwin_conversations'

const CMD_MAP: Record<string, string> = {
  '/status': 'Dame el estado actual de la maquina.',
  '/summary': 'Dame un resumen general de la maquina con tendencias y anomalias.',
  '/anomalies': 'Detecta anomalias en las variables de la maquina en las ultimas 24 horas.',
  '/events': 'Muestra los eventos recientes de la maquina de los ultimos 7 dias.',
  '/recomend': 'Dame recomendaciones de operacion y mantenimiento.',
  '/vars': 'Muestra el historial de las variables principales de la maquina en 24 horas.',
}

const HELP_MSG = `Comandos:
  /status      Estado actual
  /summary     Resumen general
  /anomalies   Anomalias (24h)
  /events      Eventos (7 dias)
  /recomend    Recomendaciones
  /vars        Historial variables
  /clear       Limpiar chat`

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

function getInitialDarkMode(): boolean {
  const saved = localStorage.getItem('darkMode')
  if (saved !== null) return saved === 'true'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [thinking, setThinking] = useState(false)
  const [darkMode, setDarkMode] = useState(getInitialDarkMode)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  const updateConversation = useCallback((id: string, msgs: Message[]) => {
    setConversations(prev => prev.map(c =>
      c.id === id
        ? { ...c, messages: msgs, title: getTitleFromMessages(msgs), updatedAt: Date.now() }
        : c
    ))
  }, [])

  const handleNewConversation = () => {
    const newConv: Conversation = {
      id: generateId(),
      title: 'Nueva conversacion',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    setConversations(prev => [newConv, ...prev])
    setActiveId(newConv.id)
    setMessages([])
    setSidebarOpen(false)
  }

  const handleSelectConversation = (id: string) => {
    const conv = conversations.find(c => c.id === id)
    if (conv) {
      setActiveId(id)
      setMessages(conv.messages)
    }
    setSidebarOpen(false)
  }

  const handleDeleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeId === id) {
      setActiveId(null)
      setMessages([])
    }
  }

  const clearChat = useCallback(async () => {
    setMessages([])
    if (activeId) {
      updateConversation(activeId, [])
    }

    try {
      await fetch('/api/clear', { method: 'POST' })
    } catch {
      // El chat visual se limpia aunque el backend no este disponible.
    }
  }, [activeId, updateConversation])

  const sendMessage = async (text: string) => {
    if (!text.trim() || thinking) return

    if (text === '/clear') {
      await clearChat()
      return
    }

    if (text === '/help') {
      const newMsgs = [...messages, { role: 'bot' as const, text: HELP_MSG }]
      setMessages(newMsgs)
      if (activeId) updateConversation(activeId, newMsgs)
      return
    }

    let currentId = activeId
    if (!currentId) {
      const newConv: Conversation = {
        id: generateId(),
        title: getTitleFromMessages([{ role: 'user', text }]),
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      }
      setConversations(prev => [newConv, ...prev])
      currentId = newConv.id
      setActiveId(currentId)
    }

    const userMsg: Message = { role: 'user', text }
    const withUser = [...messages, userMsg]
    setMessages(withUser)

    setThinking(true)
    const cmd = CMD_MAP[text]

    try {
      const res = await fetch(`/api/completion?msg=${encodeURIComponent(cmd || text)}`)
      const data: CompletionResponse = await res.json()
      const botMsg: Message = { role: 'bot', text: data.completion }
      const withBot = [...withUser, botMsg]
      setMessages(withBot)
      if (currentId) updateConversation(currentId, withBot)
    } catch {
      const errorMsg: Message = { role: 'bot', text: 'Error al conectar con el servidor.' }
      const withError = [...withUser, errorMsg]
      setMessages(withError)
      if (currentId) updateConversation(currentId, withError)
    }

    setThinking(false)
  }

  return (
    <div className="app-layout">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="chat-container">
        <header className="chat-header">
          <button
            className="menu-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Abrir historial"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <h1>MachineTwin</h1>
          <div className="header-spacer" />
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

        <MessageList
          messages={messages}
          thinking={thinking}
          messagesEndRef={messagesEndRef}
        />

        <MessageInput onSend={sendMessage} onClear={clearChat} disabled={thinking} />
      </div>
    </div>
  )
}

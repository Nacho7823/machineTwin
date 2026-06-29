import type { RefObject } from 'react'

// === Chat ===
export type MessageRole = 'user' | 'bot'

export interface Message {
  role: MessageRole
  text: string
}

export interface QuickAction {
  label: string
  prompt: string
}

export type CommandType = 'message' | 'command' | 'clear' | 'help' | 'quit'

export interface CompletionResponse {
  completion: string
}

export type AppView = 'chat' | 'traces'

// === Conversation ===
export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

export interface PersistedConversation {
  conversation_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface TraceEvent {
  timestamp?: string
  conversation_id?: string
  trace_id?: string
  event: string
  step?: number
  tool?: string
  tool_status?: string
  tool_latency_ms?: number
  llm_model?: string
  prompt_version?: string
  prompt_hash?: string
  latency_ms?: number
  finish_status?: string
  rag_chunk_count?: number
  rag_chunks?: Array<{
    doc_id?: string
    title?: string
    source_path?: string
    chunk_index?: number
    distance?: number
    preview?: string
  }>
  input?: unknown
  output?: string
  response?: unknown
}

export interface PersistedMessage {
  role: string
  content: string
  created_at: string
}

export interface ConversationTrace {
  conversation_id: string
  messages: PersistedMessage[]
  traces: TraceEvent[]
}

// === Components ===
export interface MessageListProps {
  messages: Message[]
  thinking: boolean
  messagesEndRef: RefObject<HTMLDivElement | null>
  quickActions: QuickAction[]
  onQuickPrompt: (prompt: string) => void
}

export interface MessageInputProps {
  onSend: (text: string) => void
  onClear: () => void
  disabled: boolean
}

export interface MarkdownRendererProps {
  content: string
}

export interface SidebarProps {
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
  open: boolean
  collapsed: boolean
  onClose: () => void
}

export interface TraceViewProps {
  activeConversationId: string | null
}

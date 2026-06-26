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

// === Conversation ===
export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
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

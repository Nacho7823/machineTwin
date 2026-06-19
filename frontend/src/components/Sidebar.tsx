import type { SidebarProps } from '../types'

export function Sidebar({ conversations, activeId, onSelect, onNew, onDelete, open, onClose }: SidebarProps) {
  return (
    <>
      {open && <div className="sidebar-overlay" onClick={onClose} />}
      <aside className={`sidebar ${open ? 'sidebar--open' : ''}`}>
        <div className="sidebar-header">
          <button className="sidebar-new-btn" onClick={onNew}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Nueva conversacion
          </button>
        </div>
        <div className="sidebar-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`sidebar-item ${conv.id === activeId ? 'sidebar-item--active' : ''}`}
              onClick={() => onSelect(conv.id)}
            >
              <div className="sidebar-item-content">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="sidebar-item-icon">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <span className="sidebar-item-title">{conv.title}</span>
              </div>
              <button
                className="sidebar-item-delete"
                onClick={(e) => { e.stopPropagation(); onDelete(conv.id) }}
                aria-label="Eliminar conversacion"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <div className="sidebar-empty">
              No hay conversaciones
            </div>
          )}
        </div>
      </aside>
    </>
  )
}

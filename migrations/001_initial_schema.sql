CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'Conversacion',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trace_events (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    trace_id TEXT,
    event TEXT NOT NULL,
    step INTEGER,
    tool TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON conversation_messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_traces_conversation ON trace_events(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_traces_trace_id ON trace_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_traces_event ON trace_events(event);

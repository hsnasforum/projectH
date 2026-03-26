PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Initial SQLite migration for the local AI assistant MVP.
-- This file captures the implementation-ready baseline schema.

CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  root_path TEXT NOT NULL UNIQUE,
  access_mode TEXT NOT NULL DEFAULT 'read_only'
    CHECK (access_mode IN ('read_only', 'approved_write')),
  is_enabled INTEGER NOT NULL DEFAULT 1
    CHECK (is_enabled IN (0, 1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_profiles (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL
    CHECK (provider IN ('ollama', 'llamacpp', 'openai_compatible')),
  model_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  context_window INTEGER,
  is_default INTEGER NOT NULL DEFAULT 0
    CHECK (is_default IN (0, 1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  workspace_id TEXT,
  selected_model_id TEXT,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'archived')),
  summary TEXT,
  created_at TEXT NOT NULL,
  last_active_at TEXT NOT NULL,
  FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
  FOREIGN KEY (selected_model_id) REFERENCES model_profiles(id)
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL
    CHECK (role IN ('system', 'user', 'assistant', 'tool')),
  content TEXT NOT NULL,
  tool_name TEXT,
  tool_run_id TEXT,
  token_count INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  absolute_path TEXT NOT NULL,
  mime_type TEXT,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT NOT NULL,
  last_modified_at TEXT NOT NULL,
  indexed_at TEXT,
  summary TEXT,
  UNIQUE (workspace_id, relative_path),
  FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  token_count INTEGER,
  created_at TEXT NOT NULL,
  UNIQUE (document_id, chunk_index),
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
  chunk_id UNINDEXED,
  document_id UNINDEXED,
  content,
  tokenize = 'unicode61'
);

CREATE TRIGGER IF NOT EXISTS document_chunks_ai
AFTER INSERT ON document_chunks
BEGIN
  INSERT INTO document_chunks_fts(rowid, chunk_id, document_id, content)
  VALUES (new.rowid, new.id, new.document_id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS document_chunks_ad
AFTER DELETE ON document_chunks
BEGIN
  DELETE FROM document_chunks_fts
  WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS document_chunks_au
AFTER UPDATE ON document_chunks
BEGIN
  DELETE FROM document_chunks_fts
  WHERE rowid = old.rowid;

  INSERT INTO document_chunks_fts(rowid, chunk_id, document_id, content)
  VALUES (new.rowid, new.id, new.document_id, new.content);
END;

CREATE TABLE IF NOT EXISTS approval_requests (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  tool_plan_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  action_type TEXT NOT NULL
    CHECK (action_type IN ('read', 'write', 'execute', 'network')),
  risk_level TEXT NOT NULL
    CHECK (risk_level IN ('low', 'medium', 'high')),
  reason TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  preview_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected', 'expired', 'cancelled')),
  requested_at TEXT NOT NULL,
  decided_at TEXT,
  expires_at TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  workspace_id TEXT,
  title TEXT NOT NULL,
  body_markdown TEXT NOT NULL,
  origin TEXT NOT NULL
    CHECK (origin IN ('user', 'assistant', 'mixed')),
  storage_target TEXT NOT NULL
    CHECK (storage_target IN ('app_notes', 'workspace_export')),
  requested_path TEXT,
  resolved_path TEXT,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'pending_approval', 'saved', 'failed', 'archived')),
  last_saved_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (storage_target != 'workspace_export' OR workspace_id IS NOT NULL),
  CHECK (status NOT IN ('pending_approval', 'saved') OR requested_path IS NOT NULL),
  CHECK (status != 'saved' OR resolved_path IS NOT NULL),
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
  FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS note_sources (
  id TEXT PRIMARY KEY,
  note_id TEXT NOT NULL,
  document_id TEXT,
  message_id TEXT,
  source_kind TEXT NOT NULL
    CHECK (source_kind IN ('document', 'message', 'search_result')),
  source_path TEXT,
  snippet_text TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS tool_runs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  approval_request_id TEXT,
  tool_name TEXT NOT NULL,
  mode TEXT NOT NULL
    CHECK (mode IN ('read_only', 'requires_approval')),
  side_effect_scope TEXT NOT NULL DEFAULT 'none'
    CHECK (side_effect_scope IN ('none', 'app_state', 'filesystem')),
  status TEXT NOT NULL
    CHECK (status IN ('planned', 'running', 'succeeded', 'failed', 'rejected', 'cancelled')),
  input_json TEXT NOT NULL,
  output_json TEXT,
  error_text TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL
    CHECK (actor IN ('user', 'assistant', 'system')),
  severity TEXT NOT NULL
    CHECK (severity IN ('info', 'warn', 'error')),
  session_id TEXT,
  tool_run_id TEXT,
  approval_request_id TEXT,
  message TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
  FOREIGN KEY (tool_run_id) REFERENCES tool_runs(id) ON DELETE SET NULL,
  FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_last_active_at
  ON sessions(last_active_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_session_created_at
  ON messages(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_documents_workspace_path
  ON documents(workspace_id, relative_path);

CREATE INDEX IF NOT EXISTS idx_notes_status_updated_at
  ON notes(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_notes_session_created_at
  ON notes(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_note_sources_note_id
  ON note_sources(note_id);

CREATE INDEX IF NOT EXISTS idx_approval_requests_status_requested_at
  ON approval_requests(status, requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_tool_runs_session_created_at
  ON tool_runs(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
  ON audit_logs(created_at DESC);

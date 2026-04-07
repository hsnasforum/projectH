CREATE TABLE IF NOT EXISTS raw_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dedup_key TEXT NOT NULL UNIQUE,

  ts TEXT NOT NULL,
  day TEXT NOT NULL,
  source TEXT NOT NULL,
  model TEXT,

  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cache_read_tokens INTEGER NOT NULL DEFAULT 0,
  cache_write_tokens INTEGER NOT NULL DEFAULT 0,
  thinking_tokens INTEGER NOT NULL DEFAULT 0,
  web_search_requests INTEGER NOT NULL DEFAULT 0,

  actual_cost_usd REAL,
  estimated_cost_usd REAL,

  message_id TEXT,
  request_id TEXT,

  raw_path TEXT NOT NULL,
  raw_offset INTEGER,
  raw_line_no INTEGER,
  content_hash TEXT,
  collected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collector_status (
  singleton_key INTEGER PRIMARY KEY CHECK (singleton_key = 1),
  phase TEXT NOT NULL,
  last_heartbeat_at TEXT NOT NULL,
  last_scan_started_at TEXT,
  last_scan_finished_at TEXT,
  scanned_files INTEGER NOT NULL DEFAULT 0,
  parsed_events INTEGER NOT NULL DEFAULT 0,
  last_error TEXT
);

CREATE TABLE IF NOT EXISTS file_state (
  path TEXT PRIMARY KEY,
  parser_kind TEXT NOT NULL,
  mtime_ns INTEGER NOT NULL,
  size INTEGER NOT NULL,
  last_offset INTEGER,
  last_line_no INTEGER,
  last_scanned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_event (
  event_key TEXT PRIMARY KEY,

  ts TEXT NOT NULL,
  job_id TEXT NOT NULL,
  round INTEGER,
  event_type TEXT NOT NULL,
  slot TEXT,
  agent TEXT,
  pane_target TEXT,
  artifact_path TEXT,
  raw_path TEXT NOT NULL,
  raw_line_no INTEGER,
  log_family TEXT,
  payload_json TEXT
);

CREATE TABLE IF NOT EXISTS job_usage_link (
  job_id TEXT NOT NULL,
  usage_id INTEGER NOT NULL,
  link_method TEXT NOT NULL,
  confidence REAL NOT NULL,
  linked_at TEXT,
  note TEXT,

  PRIMARY KEY (job_id, usage_id),
  FOREIGN KEY (usage_id) REFERENCES raw_usage(id)
);

CREATE INDEX IF NOT EXISTS idx_raw_usage_day_source ON raw_usage(day, source);
CREATE INDEX IF NOT EXISTS idx_raw_usage_ts ON raw_usage(ts);
CREATE INDEX IF NOT EXISTS idx_raw_usage_source_ts ON raw_usage(source, ts);
CREATE INDEX IF NOT EXISTS idx_raw_usage_raw_path ON raw_usage(raw_path);
CREATE INDEX IF NOT EXISTS idx_pipeline_event_job_ts ON pipeline_event(job_id, ts);
CREATE INDEX IF NOT EXISTS idx_pipeline_event_agent_ts ON pipeline_event(agent, ts);
CREATE INDEX IF NOT EXISTS idx_pipeline_event_job_id ON pipeline_event(job_id);
CREATE INDEX IF NOT EXISTS idx_job_usage_link_job ON job_usage_link(job_id);

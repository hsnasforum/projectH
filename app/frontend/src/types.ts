export interface SessionSummary {
  session_id: string;
  title: string;
  updated_at: string;
  created_at: string;
  message_count: number;
  pending_approval_count: number;
  last_message_preview: string;
}

export interface Message {
  message_id: string;
  role: "user" | "assistant";
  text: string;
  timestamp?: string;
  status?: string;
  artifact_id?: string;
  artifact_kind?: string;
  response_origin?: ResponseOrigin;
  evidence?: EvidenceItem[];
  summary_chunks?: SummaryChunk[];
  claim_coverage?: ClaimCoverageItem[];
  corrected_text?: string;
  corrected_outcome?: Record<string, unknown>;
  source_type_label?: string;
  source_filename_label?: string;
  search_results?: SearchResult[];
  applied_preferences?: { description: string; fingerprint: string }[];
  feedback?: string;
  content_verdict?: string;
  content_reason_record?: ContentReasonRecord;
}

export interface ResponseOrigin {
  provider?: string;
  badge?: string;
  label?: string;
  kind?: string;
  answer_mode?: string;
  verification_label?: string;
  source_roles?: SourceRoleItem[];
}

export interface SourceRoleItem {
  role: string;
  trust_level?: string;
}

export interface EvidenceItem {
  label: string;
  text: string;
  source_role?: string;
}

export interface SummaryChunk {
  index?: number;
  text: string;
  position_label?: string;
}

export interface ClaimCoverageItem {
  slot: string;
  status: string;
  value?: string;
  source_role?: string;
  source_title?: string;
  hint?: string;
  trusted_source_count?: number;
}

export interface ContentReasonRecord {
  reason_scope: string;
  reason_label: string;
  reason_note?: string;
  recorded_at: string;
  artifact_id: string;
  source_message_id: string;
}

export interface SearchResult {
  path: string;
  matched_on: string;
  snippet?: string;
}

export interface PendingApproval {
  approval_id: string;
  kind: string;
  requested_path: string;
  overwrite: boolean;
  preview_markdown: string;
  source_paths: string[];
  created_at: string;
  artifact_id?: string;
  source_message_id?: string;
  save_content_source?: string;
  action_kind?: string;
  target_id?: string;
  audit_trace_required?: boolean;
  is_reversible?: boolean;
}

export interface Session {
  session_id: string;
  title: string;
  messages: Message[];
  pending_approvals: PendingApproval[];
  permissions: { web_search: string };
  active_context?: Record<string, unknown>;
  review_queue_items?: unknown[];
  recurrence_aggregate_candidates?: unknown[];
}

export interface ChatResponse {
  ok: boolean;
  response?: {
    text: string;
    status: string;
    message_id?: string;
    actions_taken?: string[];
    evidence?: EvidenceItem[];
    summary_chunks?: SummaryChunk[];
    claim_coverage?: ClaimCoverageItem[];
    approval?: PendingApproval;
    active_context?: Record<string, unknown>;
    follow_up_suggestions?: string[];
    response_origin?: ResponseOrigin;
    artifact_id?: string;
    artifact_kind?: string;
    search_results?: SearchResult[];
    web_search_record_path?: string;
    saved_note_path?: string;
    applied_preferences?: { description: string; fingerprint: string }[];
  };
  session?: Session;
  error?: { message: string };
}

export interface StreamEvent {
  ok?: boolean;
  event: string;
  data?: ChatResponse;
  text?: string;
  phase?: string;
  title?: string;
  detail?: string;
  note?: string;
  provider?: string;
  reachable?: boolean;
  badge?: string;
  label?: string;
  kind?: string;
  answer_mode?: string;
}

export interface AppSettings {
  provider: string;
  model: string;
  baseUrl: string;
  searchLimit: number;
  notePath: string;
  webSearchPermission: string;
  skipPreflight: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
  provider: "ollama",
  model: "auto",
  baseUrl: "http://localhost:11434",
  searchLimit: 3,
  notePath: "",
  webSearchPermission: "enabled",
  skipPreflight: false,
};

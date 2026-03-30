# API and Tool Interface Draft

## 1. API Design Rules

1. All endpoints are local-only and served from the same Next.js app.
2. The UI never talks to model runtimes or the filesystem directly.
3. Read operations are the default; risky operations go through approval records.
4. Chat responses should support streaming so the UI feels responsive on local hardware.
5. Every tool plan and execution result must be loggable.
6. Note drafts can exist before a save path is chosen; path validation happens again at save execution time.

## 2. Suggested HTTP Surface

### Session and chat APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Local readiness check for UI boot |
| `GET` | `/api/models` | List configured local model profiles |
| `POST` | `/api/sessions` | Create a new chat session |
| `GET` | `/api/sessions` | List recent sessions |
| `GET` | `/api/sessions/:sessionId` | Load transcript, tool runs, and approvals |
| `POST` | `/api/sessions/:sessionId/messages/stream` | Send a user message and stream assistant events |

### Workspace and search APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/workspaces` | List allowlisted workspace roots |
| `POST` | `/api/workspaces` | Register a new workspace root |
| `POST` | `/api/workspaces/:workspaceId/index` | Start or refresh indexing |
| `POST` | `/api/search` | Search indexed documents |
| `GET` | `/api/files/content` | Read a single file from an allowed path |

### Notes APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/notes` | List note drafts and saved notes |
| `POST` | `/api/notes/drafts` | Create or update a note draft in SQLite |
| `GET` | `/api/notes/:noteId` | Load note body, sources, and save status |
| `POST` | `/api/notes/:noteId/save-request` | Create an approval request to save or overwrite a note file |

### Approval and logs APIs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/approvals` | List pending and recent approval requests |
| `POST` | `/api/approvals/:approvalId/decision` | Approve or reject a pending action |
| `GET` | `/api/tool-runs` | List tool execution history |
| `GET` | `/api/logs` | Query structured audit logs |

## 3. Streaming Event Contract

`POST /api/sessions/:sessionId/messages/stream` should return server-sent events or chunked JSON events with a small event vocabulary:

```ts
type ChatStreamEvent =
  | { type: 'message.started'; messageId: string }
  | { type: 'message.delta'; messageId: string; textDelta: string }
  | { type: 'tool.planned'; toolPlan: ToolPlan }
  | { type: 'approval.required'; approval: ApprovalRequest }
  | { type: 'note.draft.created'; note: NoteRecord }
  | { type: 'tool.started'; toolRunId: string; toolName: string }
  | { type: 'tool.completed'; toolRun: ToolRunResult }
  | { type: 'note.saved'; noteId: string; path: string }
  | { type: 'message.completed'; messageId: string }
  | { type: 'error'; code: string; message: string };
```

## 4. Core TypeScript Contracts

```ts
export type ToolRiskLevel = 'low' | 'medium' | 'high';

export type ToolMode = 'read_only' | 'requires_approval';

export type ToolSideEffectScope = 'none' | 'app_state' | 'filesystem';

export type ApprovalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'cancelled';

export type NoteStatus =
  | 'draft'
  | 'pending_approval'
  | 'saved'
  | 'failed'
  | 'archived';

export type NoteSaveTarget =
  | {
      storageTarget: 'app_notes';
      requestedPath?: string;
      resolvedPath?: string;
    }
  | {
      storageTarget: 'workspace_export';
      workspaceId: string;
      requestedPath?: string;
      resolvedPath?: string;
    };

export interface NoteSourceRef {
  sourceKind: 'document' | 'message' | 'search_result';
  documentId?: string;
  messageId?: string;
  sourcePath?: string;
  snippetText?: string;
  metadata?: {
    page?: number;
    chunkIndex?: number;
    parser?: string;
    [key: string]: unknown;
  };
}

export interface ToolSpec {
  name: string;
  description: string;
  mode: ToolMode;
  riskLevel: ToolRiskLevel;
  sideEffectScope: ToolSideEffectScope;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
}

export interface ToolPlan {
  id: string;
  sessionId: string;
  toolName: string;
  reason: string;
  mode: ToolMode;
  riskLevel: ToolRiskLevel;
  input: Record<string, unknown>;
  preview?: {
    affectedPaths?: string[];
    diffText?: string;
    summary: string;
  };
}

export interface ApprovalRequest {
  id: string;
  sessionId: string;
  toolPlanId: string;
  toolName: string;
  status: ApprovalStatus;
  riskLevel: ToolRiskLevel;
  reason: string;
  previewSummary: string;
  affectedPaths: string[];
  requestedAt: string;
  expiresAt?: string;
}

export interface ToolRunResult {
  id: string;
  sessionId: string;
  toolName: string;
  mode: ToolMode;
  sideEffectScope: ToolSideEffectScope;
  status: 'planned' | 'running' | 'succeeded' | 'failed' | 'rejected' | 'cancelled';
  startedAt?: string;
  finishedAt?: string;
  output?: Record<string, unknown>;
  error?: string;
}

export interface NoteRecord {
  id: string;
  sessionId?: string;
  title: string;
  bodyMarkdown: string;
  origin: 'user' | 'assistant' | 'mixed';
  saveTarget: NoteSaveTarget;
  status: NoteStatus;
  sources: NoteSourceRef[];
  createdAt: string;
  updatedAt: string;
  lastSavedAt?: string;
}
```

## 5. Model Adapter Contract

This is the seam that keeps the system replaceable when the local model runtime changes.

```ts
export interface ModelAdapter {
  id: string;
  provider: 'ollama' | 'llamacpp' | 'openai_compatible';
  listModels(): Promise<ModelProfile[]>;
  streamChat(input: ModelChatRequest): AsyncIterable<ModelChatChunk>;
  embed?(input: EmbeddingRequest): Promise<EmbeddingResponse>;
  healthCheck(): Promise<{ ok: boolean; detail?: string }>;
}

export interface ModelChatRequest {
  model: string;
  messages: Array<{ role: 'system' | 'user' | 'assistant' | 'tool'; content: string }>;
  tools?: ToolSpec[];
  maxTokens?: number;
  temperature?: number;
}
```

## 6. MVP Tool Catalog

### Tool: `fs.list`

Purpose:
List files under an allowlisted workspace path.

Input:

```ts
type FsListInput = {
  workspaceId: string;
  relativePath?: string;
  recursive?: boolean;
};
```

Mode:
`read_only`

### Tool: `fs.read`

Purpose:
Read a single text file for summarization or quoting.

Input:

```ts
type FsReadInput = {
  workspaceId: string;
  relativePath: string;
  maxBytes?: number;
};
```

Mode:
`read_only`

### Tool: `docs.search`

Purpose:
Run keyword search across indexed documents.

Input:

```ts
type DocsSearchInput = {
  workspaceId: string;
  query: string;
  limit?: number;
};
```

Mode:
`read_only`

### Tool: `docs.summarize`

Purpose:
Create a grounded summary from selected files or search hits.

Input:

```ts
type DocsSummarizeInput = {
  workspaceId: string;
  filePaths?: string[];
  searchQuery?: string;
  summaryStyle?: 'brief' | 'bullet' | 'action_items';
};
```

Mode:
`read_only`

### Tool: `notes.create_draft`

Purpose:
Create or update a note draft from user input, a document summary, or selected search results.

Input:

```ts
type NotesCreateDraftInput = {
  sessionId?: string;
  title: string;
  bodyMarkdown: string;
  origin?: 'user' | 'assistant' | 'mixed';
  sources?: NoteSourceRef[];
  saveTarget?: NoteSaveTarget;
};
```

Mode:
`read_only`

Note:
This tool does not write to the filesystem, but it does persist draft state in SQLite so the user can review it before any file write happens.

### Tool: `notes.save`

Purpose:
Write a note draft or summary to the local notes directory or an approved workspace export path.

Input:

```ts
type NotesSaveInput =
  | {
      noteId: string;
      storageTarget: 'app_notes';
      requestedPath: string;
      overwrite?: boolean;
    }
  | {
      noteId: string;
      storageTarget: 'workspace_export';
      workspaceId: string;
      requestedPath: string;
      overwrite?: boolean;
    };
```

Mode:
`requires_approval`

Note:
This is the MVP's primary approval-gated write action because it is understandable, auditable, and easy to preview. `overwrite` defaults to `false`, and the executor resolves a final safe path from the requested relative path right before writing.

## 7. Approval Policy Matrix

| Action type | Example | Default policy |
| --- | --- | --- |
| Read inside allowlisted workspace | `fs.read`, `docs.search` | Auto-allow |
| Persist note draft in app state | `notes.create_draft` | Auto-allow |
| Save note or summary file | `notes.save` | Require explicit approval |
| Delete or rename | future tool | Block in MVP unless separately added |
| Shell command execution | future tool | Not in MVP |
| Network call | future tool | Not in MVP |

## 8. Example Chat Request Lifecycle

1. UI posts a user message to `/api/sessions/:sessionId/messages/stream`.
2. Orchestrator decides whether to answer directly or emit a `tool.planned` event.
3. If the assistant creates a note draft first, the stream emits `note.draft.created`.
4. If the tool is read-only, executor runs it and emits `tool.started` then `tool.completed`.
5. If the tool requires approval, the stream emits `approval.required` and pauses.
6. UI calls `/api/approvals/:approvalId/decision`.
7. On approval, executor resumes, saves the note when relevant, and appends the final answer to the session.

## 9. Logging Shape

Each meaningful system action should be written to both structured storage and append-only logs.

```ts
export interface AuditLogEvent {
  id: string;
  eventType:
    | 'session.created'
    | 'message.sent'
    | 'note.draft.created'
    | 'note.save.requested'
    | 'note.saved'
    | 'tool.planned'
    | 'approval.requested'
    | 'approval.approved'
    | 'approval.rejected'
    | 'tool.started'
    | 'tool.completed'
    | 'tool.failed';
  actor: 'user' | 'assistant' | 'system';
  sessionId?: string;
  toolRunId?: string;
  approvalId?: string;
  severity: 'info' | 'warn' | 'error';
  message: string;
  payload: Record<string, unknown>;
  createdAt: string;
}
```

This interface is intentionally narrow so the first MVP can stay predictable while still leaving room for future adapters and tools.

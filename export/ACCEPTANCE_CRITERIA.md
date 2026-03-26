# Acceptance Criteria

## Milestone 1: Project Control Layer
Done when:
- `AGENTS.md` exists and reflects current project direction
- Codex config exists with safe default settings
- Claude settings exist if Claude support is desired
- planner and reviewer subagents exist
- MVP scope, security, and release skills exist

## Milestone 2: First Vertical Slice
Done when:
- a local text or markdown file can be read
- the system can produce a summary through the model adapter interface
- a summary can be saved as a new markdown note only after explicit approval
- task logs are written locally
- session state can be persisted locally

## Milestone 3: Basic Search + Multi-file Flow
Done when:
- filename search works
- content search works for text-based files
- multiple documents can be summarized at a basic level
- results are logged and auditable

## Quality Gates

A change is not complete if:
- it silently widens scope
- it adds hidden destructive behavior
- it claims verification that was not actually run
- it hard-codes one provider without necessity
- it makes future commercial packaging materially harder

# Project Mission

Build a local-first AI assistant MVP for personal document work.

The product should help users read, summarize, search, organize, and save information from local files while keeping data on-device by default and requiring explicit approval for risky actions.

## Product Priorities

Priority order:
1. Local-first behavior
2. Safe, approval-based actions
3. Practical document productivity
4. Clear commercial/IP path
5. Replaceable model/runtime architecture
6. Small, testable MVP scope

## MVP Scope

The MVP should support:
- chat-based interaction
- local file reading
- document summarization
- document search
- session persistence
- approval-based write actions
- task logs

## Explicit Non-Goals

Do not add these to the MVP unless explicitly requested:
- wake-word voice assistant
- mobile app
- messenger integrations
- autonomous destructive actions
- browser login automation
- always-on background agents
- large-scale independent pretraining
- unnecessary cloud-only dependencies

## Working Style

When handling a task:
1. understand the real goal
2. decide whether the request is in scope
3. inspect relevant files and current structure first
4. propose the smallest defensible change
5. implement only what is needed
6. verify the result narrowly and concretely
7. report what changed, why, risks, and verification

Do not silently widen scope.
Do not replace simple solutions with broad rewrites unless there is a clear structural reason.

## Communication Rules

- Respond to the user in Korean honorifics.
- Separate facts, assumptions, and recommendations when useful.
- If something is uncertain, state the uncertainty explicitly.
- If one missing detail is essential, ask at most one focused clarification question.
- Otherwise proceed with a clearly stated assumption and a reversible approach.

For implementation work, always summarize:
1. goal understood
2. files or modules affected
3. proposed change
4. risk or tradeoff
5. verification method or result

## Safety Rules

Default behavior should be read-heavy and approval-based.
Treat these as risky actions:
- file overwrite
- file deletion
- file move/rename
- shell execution
- external network access
- background automation
- changes outside the project or approved working directory

Rules:
- Never introduce silent destructive behavior.
- Never automate deletion by default.
- Require explicit approval for risky actions.
- Prefer creating new files over overwriting existing files.
- Preserve logs for user-visible actions where practical.

## Architecture Rules

Preserve separation of concerns:
- UI layer
- agent/orchestration layer
- tools/actions layer
- storage/memory layer
- model/runtime adapter layer

Design for replaceability:
- model provider should be swappable
- runtime should not be hard-wired to one vendor
- storage choices should remain simple and local-first in early stages
- tool interfaces should be explicit and auditable

## Commercial and IP Rules

Always distinguish between:
1. code license
2. model license
3. asset/data license
4. trademark/branding

Rules:
- do not assume “open source” means unrestricted commercial packaging
- avoid product naming that depends on third-party project brands
- prefer original product identity, UX, workflow, and packaging
- flag licensing or trademark risks when relevant
- document third-party license obligations when introducing dependencies

## Verification Rules

After changes:
- run the narrowest relevant check first
- do not claim tests were run if they were not
- if no automated test exists, provide a short manual verification checklist
- mention known gaps honestly

Verification summary should include:
1. what was checked
2. what passed
3. what was not checked
4. remaining risks

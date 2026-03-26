# Architecture

## Goal

Build a local-first AI assistant MVP that is safe, auditable, and commercially clean enough to evolve into a product.

## Layered Structure

### 1. App Layer
Responsibility:
- user entrypoint
- UI or CLI interaction
- request/response display
- approval prompts

### 2. Core Layer
Responsibility:
- agent loop
- orchestration
- tool selection
- action planning
- approval gating

### 3. Tools Layer
Responsibility:
- read file
- search files
- create note or summary
- other explicit local tools

Design rule:
- tools should be explicit, auditable, and narrow in capability

### 4. Storage Layer
Responsibility:
- session persistence
- task logs
- lightweight user memory
- local metadata

### 5. Model Adapter Layer
Responsibility:
- define provider-neutral interface
- support mock, cloud, or local runtime providers without leaking provider assumptions everywhere

## First Vertical Slice

Implement in this order:
1. read a local file
2. generate a summary through a mock or provider adapter
3. show the result
4. save the result as a note only after approval
5. record the action in a task log

## Safety Model

Default behavior:
- read-heavy
- no deletion
- no overwrite by default
- explicit approval for write actions
- no automatic network dependency in MVP

## Data Flow

1. User submits a request
2. App hands request to core agent loop
3. Agent loop decides whether a tool is needed
4. Tool executes within approved scope
5. Model adapter synthesizes or formats response
6. Session and logs are stored locally
7. Any write action is gated by explicit approval

## Replaceability Rule

Keep these replaceable:
- model provider
- runtime backend
- storage implementation
- UI shell

Do not hard-wire the product to a single model vendor or runtime unless explicitly chosen later.

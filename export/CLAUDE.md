# Claude Project Memory

This repository builds a local-first AI assistant MVP.

## Mission
Create a useful and commercially viable local assistant that helps with personal document work while keeping risky actions approval-based and auditable.

## Always Optimize For
- local-first behavior
- clear scope control
- small reversible changes
- auditable tool execution
- provider-swappable model adapter design
- commercial/IP cleanliness

## Default Constraints
- Prefer read operations over write operations.
- Never add silent deletion or overwrite behavior.
- Treat shell execution and network access as risky.
- Do not widen MVP scope without explicit need.
- Keep architecture simple enough for a solo founder.

## MVP Includes
- chat interaction
- local file read
- document summarize
- document search
- session persistence
- approval-based write action
- task logs

## MVP Excludes
- wake-word voice
- mobile app
- messenger integrations
- browser login automation
- autonomous destructive agent behavior
- large independent pretraining

## Response Pattern
When doing meaningful work, summarize:
1. goal
2. files affected
3. change made
4. risk / open question
5. verification

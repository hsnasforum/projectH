---
name: mvp-scope
description: Use when turning a rough product direction into repo-specific current MVP scope, long-term north-star roadmap, milestones, and document updates for projectH.
---

# MVP Scope Skill

Use this skill when the user is reshaping product direction, narrowing MVP scope, or asking for milestone/acceptance rewrites.

## When To Use
- product direction reset
- MVP scoping
- milestone or acceptance-criteria cleanup
- proposal/spec alignment work

Do not use for ordinary code edits unless the task is fundamentally about scope definition.

## Expected Input
- user goal or rough product idea
- current implementation reality
- constraints such as local-first, approval-based safety, commercial/IP-safe positioning

## Expected Output
1. one-line product definition
2. current phase definition
3. next phase definition
4. long-term north star
5. target users
6. in-scope features
7. explicit non-goals
8. milestone split
9. acceptance criteria
10. open questions
11. exact docs that must be updated

## Repo-Specific Rules
- Keep `projectH` centered on a local-first document assistant.
- Treat the current document-first MVP as the first stage of a teachable local personal agent, not as the final product identity.
- Treat web search as a guarded investigation mode, not the core product identity.
- Do not frame proprietary model development or program control as the current MVP unless explicitly requested.
- When roadmap work is requested, keep current shipped behavior, next stage, and long-term north star clearly separated.

## Document Update Range
When this skill is used, check whether these files should change together:
- `docs/project-brief.md`
- `docs/PRODUCT_PROPOSAL.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `plandoc/*.md` when staged roadmap work is part of the task

## Output Style
- cut aggressively
- separate current implementation from future ambition and long-term aspiration
- call out what is implemented, in progress, not implemented, and still open

# 2026-04-20 G7 dispatcher repoint Vector 2 (Reverse-walk) Arbitration

## Context
- **Status**: Vector 1 (`VERIFY single-path lock-in`) was successfully closed in seq 527 (RESOLVE-B).
- **Remaining Risk**: Vector 2 (`4/18 WORK reverse-walk`) remains open. Currently, `latest_round_markdown` relies solely on `mtime`, allowing an older work file to be mistakenly selected as "latest" if its modification time is spoofed or updated by unrelated events.
- **Goal**: Hardening the dispatcher to prioritize chronological order (date) over file system `mtime`.

## Decision: RECOMMEND: implement dispatcher-repoint vector 2
This slice completes the `FIX_DISPATCHER_REPOINT` family by closing the reverse-walk defect vector. It is the most logical next step to ensure that the pipeline's "forward-only" progress is structurally guaranteed by the code, not just by convention.

## Execution Strategy
1. **Target**: `pipeline_runtime/schema.py:latest_round_markdown`.
2. **Logic Change**:
   - Extract year/month/day from the file path/name.
   - Change comparison key from `mtime` to `(year, month, day, mtime)`.
   - Ensure a file in `4/20` directory is always preferred over `4/18` regardless of `mtime`.
3. **Verification**:
   - Add `test_latest_round_markdown_prefers_newer_date_over_newer_mtime` to `tests/test_pipeline_runtime_schema.py`.
   - Setup fixture: `4/18` file with high `mtime`, `4/20` file with low `mtime`.
   - Assert `4/20` is returned.

## Alternatives Considered
- **G7-gate-blocking**: Deferred. Fixing the underlying dispatch bug is a higher priority than hardening the gate policy.
- **G11 (Adoption Audit)**: Deferred. Internal cleanup can wait until functional defects are closed.
- **PIVOT to docs-only**: Rejected. Current focus is on pipeline integrity.

## Risk Assessment
- Low. This is a surgical update to a utility function with strong unit test coverage.
- The change improves consistency across both `work` and `verify` (fallback) path resolution.

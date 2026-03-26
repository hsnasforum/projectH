# Next Steps

## Immediate Implementation Order
1. Expand `tools/file_reader.py` to support `.txt` and `.md` cleanly, then define the PDF strategy
2. Add a real approval flow object in `core/` instead of the boolean shortcut
3. Add `tools/file_search.py` into the agent loop
4. Add a first real provider adapter behind `model_adapter/`
5. Add manual verification notes for write-approval and log integrity

## Recommended First Ticket
Implement a command or UI flow that takes:
- input file path
- summary request
- optional output note path
- approval step before save

## Recommended Review Gate
Before adding any new capability, check:
- Does it widen MVP scope?
- Does it add hidden write or destructive behavior?
- Does it hard-code a provider?
- Does it make commercial packaging harder?

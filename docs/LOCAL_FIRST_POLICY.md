# Local-First Policy

This project assumes local-first behavior unless explicitly changed.

## Defaults
- store sessions locally
- store logs locally
- prefer local file operations only
- avoid mandatory network paths
- avoid vendor lock-in in architecture

## Allowed Exceptions
Exceptions require explicit project-level decision:
- cloud inference
- remote sync
- background telemetry
- third-party hosted storage

## Why This Exists
- privacy posture
- commercial flexibility
- clearer user trust model
- easier on-device product positioning

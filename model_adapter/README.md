# Model Adapter Layer

This layer hides provider-specific behavior behind a small interface.
Start with a mock adapter, then add local or cloud providers later.

Current providers:

- `mock`: deterministic local placeholder for early development
- `ollama`: local HTTP runtime adapter with health check, version check, and model availability preflight

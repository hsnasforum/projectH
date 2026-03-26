# Setup Notes

## Why Ollama Is Not in the Default Project Config

Ollama is useful as an optional local provider, but it should not be the default project assumption at the earliest planning stage.

Reason:
- the project should stay provider-swappable
- the team may want to prototype against a mock adapter first
- Codex config should remain conservative until local inference testing is actually needed

Use `.codex/config.ollama.optional.toml` when local runtime testing becomes part of the active milestone.

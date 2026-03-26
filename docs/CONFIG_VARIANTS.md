# Config Variants

## 1. `config.default.toml`
Use when:
- you want a neutral starting point
- you do not want to lock the project to one runtime yet
- you want workspace write + no network

## 2. `config.ollama.optional.toml`
Use when:
- local model testing has started
- Ollama is running locally
- you plan to use Codex in `--oss` mode
- you still want the rest of the project to stay provider-isolated

## 3. `config.secure.no-network.toml`
Use when:
- planning or review work only
- no file changes should occur
- you want a stricter read-only inspection mode

## Recommended default
Start with `config.default.toml`.
Move to `config.ollama.optional.toml` only after local inference integration begins.
Use `config.secure.no-network.toml` for review-heavy or audit-heavy sessions.

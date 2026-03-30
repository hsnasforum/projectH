# 2026-03-28 official Ollama runtime switch

## 변경 파일
- `/home/xpdlqj/.bashrc`
- `/home/xpdlqj/.config/systemd/user/ollama.service`
- `work/3/28/2026-03-28-official-ollama-runtime-switch.md`

## 사용 skill
- `security-gate`: 로컬 런타임 교체, 사용자 서비스 등록, shell 실행, 모델 저장소 복사, GPU 사용 검증이 승인/로그/로컬 경계를 넘지 않는지 확인했습니다.
- `release-check`: 실제 실행한 시스템 명령과 검증만 기준으로 전환 상태를 정리했습니다.
- `work-log-closeout`: 이번 operator runtime 전환 작업을 `/work` 형식으로 남겼습니다.

## 변경 이유
- 기존 snap Ollama는 같은 `qwen2.5:3b` 모델 요청에서도 `PROCESSOR 100% CPU`로 동작했습니다.
- 공식 Ollama 바이너리 경로에서는 같은 하드웨어에서 CUDA와 GPU offload가 확인되어, projectH의 로컬 런타임을 공식 Ollama 기준으로 전환할 필요가 있었습니다.

## 핵심 변경
- 기존 snap 모델 저장소를 `~/.ollama/models`로 복사해 공식 Ollama가 재다운로드 없이 같은 모델을 읽을 수 있게 했습니다.
- snap Ollama를 중지 후 제거했습니다.
- 공식 Ollama 바이너리를 `~/.local/bin/ollama`로 우선 연결했습니다.
- `~/.config/systemd/user/ollama.service`를 추가해 공식 Ollama를 `127.0.0.1:11434` 사용자 서비스로 등록했습니다.
- `~/.bashrc`에 `LOCAL_AI_MODEL_PROVIDER=ollama`, `LOCAL_AI_OLLAMA_MODEL=qwen2.5:3b`, `LOCAL_AI_OLLAMA_BASE_URL=http://127.0.0.1:11434`를 추가했습니다.
- `python3 -m app.web`를 `ollama` 기본값으로 다시 띄워 `http://127.0.0.1:8765/api/config`에서 기본 provider/model/base_url이 공식 Ollama 기준으로 보이게 했습니다.

## 검증
- `nvidia-smi`
- `ollama ps`
- `ollama list`
- `python3 -m app.main README.md --provider ollama --model qwen2.5:3b --base-url http://127.0.0.1:11435 --show-preview`
- `sudo snap stop ollama`
- `sudo snap remove ollama`
- `systemctl --user daemon-reload`
- `systemctl --user enable --now ollama`
- `systemctl --user status ollama --no-pager`
- `curl -s http://127.0.0.1:11434/api/tags`
- `curl -s http://127.0.0.1:8765/api/config`
- `python3 -m app.web` with explicit Ollama env

## 남은 리스크
- 공식 Ollama 서비스에서는 GPU 경로와 `ollama ps -> 100% GPU`를 확인했지만, `python3 -m app.main ...` 첫 호출 중 한 번 `unexpected EOF`가 발생했습니다.
- 이후에는 `journalctl --user -u ollama`에 `/api/generate` 200 응답과 GPU runner 로그가 남아 있어 일회성 워밍업/런타임 불안정 가능성이 큽니다.
- 웹 서버는 현재 세션에서 foreground로 실행 중이므로, 새 셸을 열거나 별도 서비스화하지 않으면 이 세션 종료 시 함께 내려갑니다.

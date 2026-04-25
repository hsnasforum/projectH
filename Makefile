.PHONY: run test e2e-install e2e-test controller-test eval eval-mock

run:
	python -m app.main

test:
	python -m unittest discover -s tests -p 'test_*.py'

e2e-install:
	cd e2e && npm install && npx playwright install

e2e-test:
	@E2E_DB=$$(mktemp -d)/test.db; \
	LOCAL_AI_MODEL_PROVIDER=mock LOCAL_AI_OLLAMA_MODEL= LOCAL_AI_MOCK_STREAM_DELAY_MS=10 \
	LOCAL_AI_SQLITE_DB_PATH=$$E2E_DB \
	python3 -m app.web --host 127.0.0.1 --port 8879 & \
	SERVER_PID=$$!; \
	sleep 3; \
	cd e2e && npm test; \
	EXIT_CODE=$$?; \
	kill $$SERVER_PID 2>/dev/null; \
	exit $$EXIT_CODE

controller-test:
	cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line

eval-mock:
	python -m eval.harness --provider mock --save

eval:
	python -m eval.harness --provider ollama --save

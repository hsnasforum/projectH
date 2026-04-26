.PHONY: run test e2e-install e2e-test controller-test eval eval-mock

run:
	python -m app.main

test:
	python -m unittest discover -s tests -p 'test_*.py'

e2e-install:
	cd e2e && npm install && npx playwright install

e2e-test:
	e2e/start-server.sh

controller-test:
	cd e2e && npx playwright test -c playwright.controller.config.mjs --reporter=line

eval-mock:
	python -m eval.harness --provider mock --save

eval:
	python -m eval.harness --provider ollama --save

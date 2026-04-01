.PHONY: run test e2e-install e2e-test eval eval-mock

run:
	python -m app.main

test:
	python -m unittest discover -s tests -p 'test_*.py'

e2e-install:
	cd e2e && npm install && npx playwright install

e2e-test:
	cd e2e && npm test

eval-mock:
	python -m eval.harness --provider mock --save

eval:
	python -m eval.harness --provider ollama --save

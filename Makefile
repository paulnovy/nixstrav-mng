.PHONY: test run format

test:
	pytest -q

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

format:
	@echo "No formatter configured."

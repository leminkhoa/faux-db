.PHONY: run-tests

run-tests:
	uv run pytest --cov=kuriboh --cov-report=term-missing tests

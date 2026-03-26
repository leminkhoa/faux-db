.PHONY: run-tests

run-tests:
	uv run pytest --cov=faux --cov-report=term-missing tests

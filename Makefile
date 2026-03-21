.PHONY: run-tests

run-tests:
	pytest --cov=kuriboh --cov-report=term-missing tests

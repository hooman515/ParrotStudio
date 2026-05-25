.PHONY: test test-backend build-backend build-app run clean

PYTHON ?= python3
APP_PACKAGE := frontend/macos/ParrotStudioApp

test: test-backend

test-backend:
	PYTHONPATH=backend $(PYTHON) -m unittest discover -s tests -p 'test_*.py'

build-backend:
	PYTHONPATH=backend $(PYTHON) -m parrot_studio.main --check

build-app:
	swift build --package-path $(APP_PACKAGE)

run:
	./script/build_and_run.sh

clean:
	rm -rf .build dist $(APP_PACKAGE)/.build

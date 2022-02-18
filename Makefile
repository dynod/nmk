.SILENT:
SHELL := /bin/bash

# Some defs
REQS := requirements.txt
VENV := venv
IN_VENV := source loadme.sh &&
SRC := src
OUT := out
FLAKE_REPORT := $(OUT)/flake-report/index.html
PYTHON_FILES := $(shell find $(SRC) -name '*.py')
GIT_VERSION := $(shell git describe --tags 2>/dev/null || true)
VERSION := $(shell echo "$(GIT_VERSION)" | sed -e "s/\(.*\)-\([0-9]*\)-\(.*\)/\1.post\2+\3/")
ARTIFACTS := $(OUT)/artifacts
PYTHON_DIST := $(ARTIFACTS)/nmk-$(VERSION).tar.gz
SETUP := setup.cfg

# Default target
.PHONY: default
default: build

# Clean
.PHONY: clean
clean:
	git clean -fdX

# Venv build
$(VENV): $(REQS)
	$(IN_VENV) pip install -r $(REQS)
	touch venv

# Venv clean
.PHONY: clean-venv
clean-venv:
	rm -Rf $(VENV)

# Setup file
.PHONY: $(SETUP)
$(SETUP):
	cat template-$(SETUP) | sed -e "s/{VERSION}/$(VERSION)/g" > $(SETUP)

# Flake8
$(FLAKE_REPORT): $(PYTHON_FILES)
	$(IN_VENV) black -l 160 $(SRC)
	$(IN_VENV) isort $(SRC)
	rm -Rf `dirname $(FLAKE_REPORT)`
	mkdir -p `dirname $(FLAKE_REPORT)`
	$(IN_VENV) flake8 $(SRC)

# Build
.PHONY: build
build: $(PYTHON_DIST)
$(PYTHON_DIST): $(VENV) $(SETUP) $(FLAKE_REPORT) $(PYTHON_FILES)
	$(IN_VENV) python setup.py sdist --dist-dir $(ARTIFACTS)
	$(IN_VENV) pip install $(PYTHON_DIST)

# Test
.PHONY: tests
tests:
	rm -Rf $(OUT)/tests
	$(IN_VENV) pytest --cov-fail-under=100

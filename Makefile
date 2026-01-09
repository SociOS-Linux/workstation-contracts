SHELL := /usr/bin/env bash

.PHONY: help validate deps

help:
	@printf "Targets:\n  make deps      # install validator deps\n  make validate   # validate all example contracts\n"

deps:
	@python3 -m pip install -U pip >/dev/null
	@python3 -m pip install jsonschema >/dev/null

validate:
	@./tools/validate_contract.py examples/*.json

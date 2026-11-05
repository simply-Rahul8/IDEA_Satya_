# Thin wrapper; scripts/run.py is the source of truth (Windows hosts have no make).
.PHONY: test lint format bench dev
test lint format bench dev:
	python scripts/run.py $@

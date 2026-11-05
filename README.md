# Satya

Private repo. Claim-safe beauty listing engine for Indian D2C brands. Plan: `docs/PLAN.md`. Agent rules: `AGENTS.md`. Decisions: `docs/ARCHITECTURE.md`.

Setup needs [uv](https://docs.astral.sh/uv/) (it fetches Python 3.12).

```
uv sync
python scripts/run.py test     # or: make test   (SATYA_LLM=mock)
python scripts/run.py lint
python scripts/run.py bench    # stub
python scripts/run.py dev      # uvicorn on :8000, /healthz
```

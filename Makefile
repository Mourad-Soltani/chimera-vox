.RECIPEPREFIX = >
.PHONY: install dev test lint format health clean

install:
> pip install -e .

dev:
> pip install -e ".[dev]"

test:
> pytest -v

lint:
> ruff check chimera_vox tests

format:
> ruff format chimera_vox tests

health:
> chimera-vox health

clean:
> rm -rf .chimera_cache .chimera_tmp *.mp4 *.mp3 .pytest_cache .mypy_cache .ruff_cache
> find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

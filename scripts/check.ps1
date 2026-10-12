# Local quality gate. Run before every commit. No CI runs in the cloud.
$ErrorActionPreference = "Stop"

python scripts/gen_ucd_tables.py --check
ruff format --check .
ruff check .
mypy --strict src
pytest

#!/usr/bin/env bash
# scripts/ci_check.sh
# 本地 CI 检查：black / isort / flake8 / mypy / pytest

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

source "$BACKEND_DIR/.venv/bin/activate"

echo "==> black --check backend/"
black --check "$BACKEND_DIR"

echo "==> isort --check-only backend/"
isort --check-only "$BACKEND_DIR"

echo "==> flake8 backend/"
flake8 "$BACKEND_DIR"

echo "==> mypy backend/"
cd "$BACKEND_DIR"
mypy . --ignore-missing-imports

echo "==> bandit -r app tests/"
bandit -r app tests -ll -f json -o "$PROJECT_ROOT/reports/bandit-report.json" || true
bandit -r app tests -ll

echo "==> pytest -q"
pytest -q

echo ""
echo "All checks passed."

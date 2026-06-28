#!/usr/bin/env bash
#
# demo.sh — reset to clean sample data and launch the McBride Construction demo.
#
# Resets the database, applies migrations, reseeds the sample listings + admin
# user, then starts the dev server at http://localhost:5000.
#
# Usage:
#   ./demo.sh           # reset DB, reseed, and run the server
#   ./demo.sh --no-reset # skip the DB reset; just (migrate, seed, and) run
#
set -euo pipefail

# Always operate relative to this script's location, regardless of CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/sol_main"
VENV="$SCRIPT_DIR/venv"
DB="$APP_DIR/instance/solomon.db"

RESET=1
if [[ "${1:-}" == "--no-reset" ]]; then
    RESET=0
fi

# Activate the project virtualenv.
if [[ ! -f "$VENV/bin/activate" ]]; then
    echo "ERROR: virtualenv not found at $VENV" >&2
    echo "Create it with: python3 -m venv venv && venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

cd "$APP_DIR"
export FLASK_APP=app.py

if [[ "$RESET" -eq 1 ]]; then
    echo ">> Resetting database..."
    rm -f "$DB"
fi

echo ">> Applying migrations..."
flask db upgrade

echo ">> Seeding sample data..."
python seed.py

echo ""
echo "=================================================="
echo "  McBride Construction demo is starting"
echo "  URL:    http://localhost:5000"
echo "  Admin:  admin / changeme"
echo "  Stop:   Ctrl+C"
echo "=================================================="
echo ""

exec python app.py

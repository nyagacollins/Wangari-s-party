#!/bin/bash
set -e

# choose Python
PYTHON=""
for p in python3.12 /vercel/python3/bin/python /usr/local/bin/python3 python3.11 python3.10 python3; do
  if command -v "$p" >/dev/null 2>&1; then PYTHON="$p"; break; fi
done
[ -z "$PYTHON" ] && PYTHON=python3
echo "Using $PYTHON ($($PYTHON -V 2>&1))"

echo "Creating build environment and installing dependencies..."
$PYTHON -m venv /tmp/build-venv
. /tmp/build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "Build complete."

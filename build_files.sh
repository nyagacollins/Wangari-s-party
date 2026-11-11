#!/bin/bash
set -e
echo "Installing dependencies..."
if command -v uv >/dev/null 2>&1; then
  uv pip install --system --python /vercel/python3/bin/python -r requirements.txt 2>/dev/null || uv pip install --system -r requirements.txt
else
  python3 -m pip install --break-system-packages -r requirements.txt
fi
# pick python that can import django
PYTHON=python3
for p in /vercel/python3/bin/python /usr/local/bin/python3 python3.12 python3.11 python3.10 python3; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c "import django" >/dev/null 2>&1; then PYTHON="$p"; break; fi
done
echo "Using $PYTHON ($($PYTHON -V 2>&1))"
echo "Collecting static files..."
$PYTHON manage.py collectstatic --noinput --clear
echo "Build complete."

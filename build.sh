#!/usr/bin/env bash
# Render Native Python Build Script
set -o errexit

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo "=== Building React Frontend ==="
if command -v npm &> /dev/null; then
  cd frontend
  npm install
  npm run build
  cd ..
else
  echo "Node/npm not detected in native environment. Using existing frontend/dist bundle."
fi

echo "=== Build Complete ==="

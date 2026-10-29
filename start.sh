#!/usr/bin/env bash
# Render Startup Script
set -o errexit

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips='*'

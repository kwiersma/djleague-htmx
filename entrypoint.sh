#!/bin/bash

set -e

echo "Running migrations"
uv run ./manage.py migrate

echo "Running Django app via gunicorn"
uv run gunicorn djleague.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --workers 3

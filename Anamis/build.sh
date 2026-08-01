#!/usr/bin/env bash
# exit on error
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput  # <--- این خط باید حتماً باشد
python manage.py migrate
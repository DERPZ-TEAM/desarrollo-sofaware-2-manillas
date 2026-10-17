#!/usr/bin/env bash
# Script que Render ejecuta en cada despliegue ("Build Command": bash build.sh)
# set -o errexit: si un paso falla, se detiene el despliegue (no publica algo roto)
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Junta los CSS/JS del panel /django-admin/ en la carpeta staticfiles/
python manage.py collectstatic --no-input

# Aplica los cambios pendientes de la base de datos (crea/modifica tablas)
python manage.py migrate --no-input

# Crea admin, cliente demo y categorías si no existen (no duplica nada)
python manage.py seed_goldbracelets

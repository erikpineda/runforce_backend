# RunForce — Backend

API REST en Django + Django REST Framework para RunForce (Gimnasio Force). Consumida por la app Android nativa del proyecto.

## Estructura

```
apimovil/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── common/         # permisos, paginacion, manejo de excepciones
│   ├── accounts/       # Usuario, OTP, JWT, login Google
│   ├── runs/           # Carrera, estadisticas
│   ├── social/         # Amistad, ranking
│   └── notifications/  # Dispositivo, Notificacion, integracion OneSignal
├── static/
├── media/
├── templates/
├── docs/
├── deploy/
│   └── nginx/conf.d/runforce.conf
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yml            # base (comun)
├── docker-compose.override.yml   # dev (se carga solo)
├── docker-compose.prod.yml       # produccion (con -f explicito)
├── .env.example
└── manage.py
```

## Setup local

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements/development.txt
copy .env.example .env         # completar credenciales
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/api/v1/`. Documentacion interactiva en `http://127.0.0.1:8000/api/docs/`.

## Docker

```bash
copy .env.example .env             # completar credenciales

docker compose up -d --build       # desarrollo (runserver + autoreload) -> http://localhost:8000/api/docs/

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build   # produccion (gunicorn + Nginx) -> http://localhost/api/docs/
```

Detalle del mecanismo de merge de los tres archivos de Compose en [docs/docker.md](docs/docker.md).

## Tests

```bash
set DJANGO_SETTINGS_MODULE=config.settings.testing
python manage.py test
```

## Base de datos

Por defecto todos los entornos usan MySQL (`config/settings/base.py`), configurado via variables `DB_*` del `.env`. El entorno `testing` usa SQLite en memoria para que los tests corran rapido sin depender de una base MySQL real.

## Apps y responsabilidades

- **accounts**: modelo `Usuario` (custom user model, `USERNAME_FIELD=correo`), `CodigoOTP`, registro + verificacion OTP, login JWT, login con Google (`/auth/google`), recuperacion de password.
- **runs**: modelo `Carrera` (ritmo y calorias calculados en `save()`), historial paginado, estadisticas mensuales y comparativas.
- **social**: `Amistad` (reciproca, auto-aceptada), busqueda de corredores por pais, ranking por amigos o por pais.
- **notifications**: `Dispositivo` (player id de OneSignal), `Notificacion`, disparo automatico de push ante logros, ranking superado y solicitudes de amistad (via signals de `Carrera`/`Amistad`); comando `notificar_inactivos` para el recordatorio de 3+ dias sin correr (programar con cron).

Ver [docs/despliegue.md](docs/despliegue.md) para el despliegue en GCP (Compute Engine + Cloud SQL + Cloud Storage).

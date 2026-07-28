# Despliegue en Google Cloud Platform

## Arquitectura

- **Compute Engine** (Ubuntu): Gunicorn + Nginx + systemd.
- **Cloud SQL (MySQL)**: base de datos `runforce`.
- **Cloud Storage**: fotos de perfil (`usuarios/me/foto`). En dev se usa almacenamiento local (`media/`); en produccion, agregar `django-storages[google]` y configurar `STORAGES['default']` con el backend `storages.backends.gcloud.GoogleCloudStorage` en `config/settings/production.py`.

## Pasos

1. Crear la instancia de Cloud SQL for MySQL y anotar host/usuario/password/nombre de base de datos.
2. Crear la VM de Compute Engine (Ubuntu 22.04+), abrir el puerto 443 (y 80 solo para el reto ACME de Certbot).
3. Clonar el repo, crear virtualenv, `pip install -r requirements/production.txt`.
4. Copiar `.env.example` a `.env` y completar variables (SECRET_KEY, DB_*, EMAIL_*, GOOGLE_CLIENT_ID, ONESIGNAL_*).
5. `DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate`
6. `python manage.py collectstatic --noinput`
7. Configurar Gunicorn como servicio systemd (`gunicorn config.wsgi:application --bind unix:/run/runforce.sock`).
8. Configurar Nginx como proxy reverso hacia el socket de Gunicorn, sirviendo `staticfiles/` directamente.
9. Emitir certificado con Certbot (Let's Encrypt) y forzar HTTPS.
10. Programar el recordatorio de inactividad: `0 9 * * * DJANGO_SETTINGS_MODULE=config.settings.production /ruta/venv/bin/python manage.py notificar_inactivos` (cron) o un systemd timer equivalente.
11. Habilitar backups automaticos en Cloud SQL.

## Variables sensibles

Nunca commitear `.env`. Todas las credenciales (MySQL, SMTP, OneSignal, Google) viven solo en el `.env` del servidor.

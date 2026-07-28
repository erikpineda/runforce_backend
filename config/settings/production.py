from .base import *  # noqa: F401,F403

DEBUG = False

# Todas en True por defecto (produccion real, detras de HTTPS). Mientras no
# haya TLS (Let's Encrypt no emite certificados para una IP suelta, necesita
# dominio), poner las tres en False en el .env del servidor: con
# SESSION_COOKIE_SECURE/CSRF_COOKIE_SECURE=True el navegador nunca reenvia
# esas cookies sobre HTTP plano y el login de /admin/ (y por lo tanto el
# acceso por sesion a /api/docs/) queda roto.
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30 if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL_REDIRECT
SECURE_HSTS_PRELOAD = SECURE_SSL_REDIRECT

# Nginx (nativo, fuera de Docker) termina el TLS y le hace proxy a gunicorn
# por HTTP simple. Sin esto, Django no tiene forma de saber que la conexion
# original era HTTPS y con SECURE_SSL_REDIRECT=True entra en loop de redirects.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MIDDLEWARE = MIDDLEWARE[:2] + ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE[2:]

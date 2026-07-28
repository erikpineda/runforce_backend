# Docker: desarrollo vs. produccion con "Merge Compose files"

RunForce usa **un solo Dockerfile** y **tres archivos de Compose** que se combinan
(merge) en vez de mantener dos proyectos Docker separados. No hay servicio de
base de datos: MySQL vive en el servidor remoto (`DB_HOST` en `.env`).

```
docker-compose.yml            <- base: comun a dev y prod
docker-compose.override.yml   <- override de DESARROLLO (se carga solo)
docker-compose.prod.yml       <- override de PRODUCCION (hay que pedirlo con -f)
deploy/nginx/conf.d/runforce.conf
```

## Como funciona el merge (la idea central)

Docker Compose no elige "un archivo"; **combina varios en una sola configuracion
final**, campo por campo. Las reglas (de la pagina oficial "Merge Compose files"):

- **Valores simples** (`image`, `restart`, un `command` completo): el ultimo
  archivo listado gana, pisa al anterior.
- **Listas "concatenables"** (`ports`, `expose`, `dns`, ...): se suman.
- **Mapas con clave** (`environment`, `volumes`, `labels`): se combinan **por
  clave** (nombre de variable, o *target path* del volumen). Si dos archivos
  tocan la misma clave, gana el ultimo; si tocan claves distintas, ambas quedan.

Por eso en este proyecto:

- `docker-compose.yml` (base) declara `web.volumes: - media_volume:/app/media`.
- `docker-compose.override.yml` (dev) agrega `- .:/app` (otro *target*, `/app`).
  Compose no reemplaza el volumen de `media`, lo **agrega** — el resultado final
  tiene ambos montajes.
- `docker-compose.prod.yml` fuerza `environment: DJANGO_SETTINGS_MODULE=config.settings.production`.
  Esto es intencional: `docker-compose.yml` ya carga tu `.env` completo via
  `env_file`, y ese `.env` normalmente trae `DJANGO_SETTINGS_MODULE=config.settings.development`
  para el dia a dia. `environment:` siempre le gana a `env_file:`
  (sin importar en que archivo del merge este declarado), asi que sin este
  override explicito, produccion arrancaria por accidente en modo development
  si alguien olvida ajustar el `.env` del servidor. Lo comprobe con
  `docker compose config` antes de dejarlo asi: sin el override, `DEBUG`/
  `DJANGO_SETTINGS_MODULE` del merge de produccion salian con valores de dev.

## Los dos comandos que importan

```bash
# Desarrollo: Compose carga docker-compose.yml + docker-compose.override.yml
# AUTOMATICAMENTE (ese nombre exacto es especial para Compose).
docker compose up -d --build

# Produccion: hay que pedir el merge explicito con -f (si no, el override
# de dev se seguiria cargando solo y pisaria produccion).
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Para *ver* que configuracion final resulta del merge, sin levantar nada:

```bash
docker compose config                                              # dev
docker compose -f docker-compose.yml -f docker-compose.prod.yml config  # prod
```

Esto imprime el YAML ya combinado — es la mejor forma de entender el mecanismo
y de depurar si algo no se esta pisando como esperas.

## Diferencias resultantes entre dev y prod

| | Desarrollo (`up`) | Produccion (`-f ... -f docker-compose.prod.yml up`) |
|---|---|---|
| Proceso | `manage.py runserver` (autoreload) | `gunicorn` (definido en el `CMD` del Dockerfile) |
| Settings | `config.settings.development` | `config.settings.production` (forzado) |
| Codigo fuente | montado en vivo (`.:/app`) | horneado en la imagen (sin bind mount) |
| Puerto expuesto al host | `8000` directo | ninguno en `web`; solo `nginx` en `80` |
| Nginx | no existe | sirve `/media/` y hace proxy al resto |

## Comandos de uso diario

```bash
# Desarrollo
docker compose up -d --build      # levantar
docker compose logs -f web        # ver logs
docker compose down               # bajar

# Produccion (en el servidor)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## Pendiente para produccion real

- `ALLOWED_HOSTS` en el `.env` del servidor debe listar el dominio/IP real
  (el `.env.example` trae `localhost,127.0.0.1`).
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` en
  `False` hasta tener TLS real: Let's Encrypt no emite certificados para una
  IP suelta, necesita un dominio. Con las cookies en `Secure` pero sin HTTPS,
  el navegador nunca las reenvia y hasta el login de `/admin/` se rompe. Una
  vez que haya dominio y Certbot (ver nota al final de
  `deploy/nginx/conf.d/runforce.conf`), poner las tres en `True`.

## Documentacion (/api/docs/, /api/schema/) en produccion

Con `DEBUG=False` (development.settings.production/testing) estas rutas
requieren un usuario `is_staff`, autenticado por JWT (header `Authorization`)
o por la sesion de `/admin/` — ver [apps/common/views.py](../apps/common/views.py).
Para verla desde el navegador sin generar un token: entrar primero a
`/admin/` con un usuario staff y despues abrir `/api/docs/` (misma sesion).
En `development` (`DEBUG=True`) queda publica, sin login.

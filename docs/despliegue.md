# Despliegue en Google Cloud Platform (Docker + Nginx + GitHub Actions)

## Datos de conexion de la VM

| | |
|---|---|

| Carpeta del repo en el servidor | `/opt/runforce` |


## Arquitectura

- **Compute Engine** (Ubuntu 24.04): un solo host corre MySQL (instalado directo en el
  SO, fuera de Docker) **y** los contenedores de la app (`web` = Django/gunicorn,
  `nginx` = proxy reverso). Ver [docker.md](docker.md) para el mecanismo de
  merge de los `docker-compose*.yml`.
- **MySQL**: corre en la misma VM, fuera de Docker. El backend se conecta via
  las variables `DB_*` del `.env` del servidor.
- **Cloud Storage**: fotos de perfil (`usuarios/me/foto`). Por ahora usa
  almacenamiento local (`media/`, volumen `media_volume`); para GCS agregar
  `django-storages[google]` y configurar `STORAGES['default']` con
  `storages.backends.gcloud.GoogleCloudStorage` en `config/settings/production.py`.
- **CI/CD**: [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) —
  cada push a `main` hace SSH a la VM, `git pull` y recrea los contenedores.

## 1. Preparar la VM (una sola vez)

### 1.1 Instalar Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
# cerrar sesion y volver a entrar (o `newgrp docker`) para que aplique el grupo
```

### 1.2 Clonar el repositorio

Convencion: aplicaciones desplegadas van en `/opt/<nombre>`, no en el home del
usuario. Se necesita `sudo` solo para crear la carpeta:

```bash
sudo mkdir -p /opt/runforce
sudo chown $USER:$USER /opt/runforce
```

**Repo publico** (este proyecto): no hace falta ninguna credencial, `git
clone`/`pull` por HTTPS funciona anonimo para lectura:

```bash
git clone https://github.com/<tu-usuario>/<tu-repo>.git /opt/runforce
cd /opt/runforce
```

<details>
<summary>Si el repo fuera privado (no aplica aca, dejado como referencia)</summary>

Se necesitaria una **deploy key** (par de llaves SSH de solo lectura,
especifica para este repo — no reutilizar la llave personal):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_runforce_deploy -N "" -C "runforce-deploy-key"
cat ~/.ssh/id_ed25519_runforce_deploy.pub
```

Copiar esa clave publica a GitHub: **repo → Settings → Deploy keys → Add
deploy key** (no hace falta "Allow write access", solo lectura). Configurar
SSH para que `git` la use:

```bash
cat >> ~/.ssh/config <<'EOF'
Host github.com
  IdentityFile ~/.ssh/id_ed25519_runforce_deploy
  IdentitiesOnly yes
EOF

git clone git@github.com:<tu-usuario>/<tu-repo>.git /opt/runforce
cd /opt/runforce
```

</details>
```

### 1.3 Crear el `.env` de produccion

**Nunca se sube por git.** Se crea directo en el servidor:

```bash
cp .env.example .env
nano .env
```

Como MySQL corre en esta misma VM, usa `127.0.0.1` si el contenedor pudiera
alcanzar el host directamente — pero como el contenedor tiene su propia red,
en la practica hay dos opciones para `DB_HOST`:

- La IP externa de la VM (`136.65.217.165` en este proyecto) — funciona si el
  proveedor permite "hairpin NAT" (conectarte a tu propia IP publica desde
  adentro).
- `host.docker.internal` — ya viene resuelto en `docker-compose.yml` via
  `extra_hosts`, apunta al host sin depender de hairpin NAT. **Usa esta si la
  IP externa no conecta desde dentro del contenedor** (probalo con el comando
  de la seccion 3).

Ajusta tambien: `ALLOWED_HOSTS` (IP/dominio real), `SECRET_KEY`,
`SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` (en
`False` hasta tener TLS real — ver nota en [docker.md](docker.md)), `EMAIL_*`,
`GOOGLE_CLIENT_ID`, `ONESIGNAL_*`.

### 1.4 Primer despliegue manual

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Verificar: `http://136.65.217.165/api/docs/` (pide login staff, ver
[docker.md](docker.md)).

## 2. GitHub Actions (deploy automatico en cada push a `main`)

El workflow [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) ya
esta en el repo. Le falta la llave SSH y los secrets para poder conectarse:

### 2.1 Generar una llave SSH dedicada para Actions (distinta a la deploy key de git)

En tu maquina local (no en el servidor):

```bash
ssh-keygen -t ed25519 -f ./runforce_actions_key -N "" -C "github-actions-deploy"
```

Esto genera `runforce_actions_key` (privada) y `runforce_actions_key.pub`
(publica).

### 2.2 Autorizar esa llave en el servidor

```bash
cat runforce_actions_key.pub | ssh runforcehn@136.65.217.165 'cat >> ~/.ssh/authorized_keys'
```

### 2.3 Cargar los secrets en GitHub

**Repo → Settings → Secrets and variables → Actions → New repository secret:**


Despues de cargar los secrets, borra `runforce_actions_key` de tu maquina
local (ya quedo guardada, cifrada, del lado de GitHub).

### 2.4 Probar

Un push a `main` (o **Actions → Deploy a produccion → Run workflow** para
disparo manual) hace SSH al servidor y ejecuta: `git pull`, recrea los
contenedores con `--build`, corre `migrate`, y limpia imagenes viejas.

## 3. Verificar conectividad a MySQL desde el contenedor

Si el primer deploy falla en `migrate` con un timeout de conexion, es el
problema de hairpin NAT mencionado en 1.3:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web \
  python -c "import socket; socket.create_connection(('host.docker.internal', 3306), timeout=5); print('OK')"
```

Si eso funciona pero la IP externa no, cambia `DB_HOST=host.docker.internal`
en el `.env` del servidor y corre `docker compose -f ... up -d` de nuevo (no
hace falta `--build`, es solo una variable de entorno).

## 4. Pendientes

- TLS con Certbot una vez que haya un dominio (Let's Encrypt no emite
  certificados para IPs sueltas) — ver nota al final de
  `deploy/nginx/conf.d/runforce.conf`.
- Backups automaticos de MySQL (no esta en Cloud SQL en este proyecto, corre
  en la misma VM — programar `mysqldump` via cron).
- Recordatorio de inactividad: `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py notificar_inactivos`,
  programado con cron/systemd timer en el host (no dentro del contenedor).

# Legal AI Application Makefile
# Comandos útiles para desarrollo y despliegue

.PHONY: help setup build up down restart logs clean test lint format

# Variables
COMPOSE_FILE = docker-compose.yml
APP_NAME = legal-ai-app

# Comando por defecto
help: ## Mostrar esta ayuda
	@echo "Legal AI Application - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configurar la aplicación por primera vez
	@echo "🚀 Configurando Legal AI Application..."
	./setup.sh

build: ## Construir las imágenes de Docker
	@echo "🔨 Construyendo imágenes..."
	docker-compose -f $(COMPOSE_FILE) build

up: ## Iniciar todos los servicios
	@echo "🚀 Iniciando servicios..."
	docker-compose -f $(COMPOSE_FILE) up -d

down: ## Detener todos los servicios
	@echo "🛑 Deteniendo servicios..."
	docker-compose -f $(COMPOSE_FILE) down

restart: ## Reiniciar todos los servicios
	@echo "🔄 Reiniciando servicios..."
	docker-compose -f $(COMPOSE_FILE) restart

logs: ## Ver logs de todos los servicios
	@echo "📋 Mostrando logs..."
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-app: ## Ver logs solo de la aplicación
	@echo "📋 Mostrando logs de la aplicación..."
	docker-compose -f $(COMPOSE_FILE) logs -f app

logs-db: ## Ver logs solo de la base de datos
	@echo "📋 Mostrando logs de la base de datos..."
	docker-compose -f $(COMPOSE_FILE) logs -f postgres

logs-redis: ## Ver logs solo de Redis
	@echo "📋 Mostrando logs de Redis..."
	docker-compose -f $(COMPOSE_FILE) logs -f redis

logs-celery: ## Ver logs solo de Celery
	@echo "📋 Mostrando logs de Celery..."
	docker-compose -f $(COMPOSE_FILE) logs -f celery

status: ## Ver estado de los servicios
	@echo "📊 Estado de los servicios..."
	docker-compose -f $(COMPOSE_FILE) ps

clean: ## Limpiar contenedores, imágenes y volúmenes
	@echo "🧹 Limpiando Docker..."
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all
	docker system prune -f

clean-data: ## Limpiar solo datos (mantener imágenes)
	@echo "🧹 Limpiando datos..."
	docker-compose -f $(COMPOSE_FILE) down -v

test: ## Ejecutar tests (requiere Python local)
	@echo "🧪 Ejecutando tests..."
	python -m pytest tests/ -v

lint: ## Ejecutar linting (requiere Python local)
	@echo "🔍 Ejecutando linting..."
	flake8 app/ --max-line-length=120 --ignore=E501,W503
	black --check app/

format: ## Formatear código (requiere Python local)
	@echo "✨ Formateando código..."
	black app/ --line-length=120
	isort app/

install-dev: ## Instalar dependencias de desarrollo
	@echo "📦 Instalando dependencias de desarrollo..."
	pip install -r requirements.txt
	pip install pytest flake8 black isort

db-migrate: ## Ejecutar migraciones de base de datos
	@echo "🗄️ Ejecutando migraciones..."
	docker-compose -f $(COMPOSE_FILE) exec app python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

db-reset: ## Resetear base de datos (¡CUIDADO!)
	@echo "⚠️  Reseteando base de datos..."
	@read -p "¿Estás seguro? Esto eliminará todos los datos. (y/N): " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f $(COMPOSE_FILE) down -v; \
		docker-compose -f $(COMPOSE_FILE) up -d postgres; \
		sleep 10; \
		docker-compose -f $(COMPOSE_FILE) up -d; \
		echo "✅ Base de datos reseteada"; \
	else \
		echo "❌ Operación cancelada"; \
	fi

import-data: ## Importar datos iniciales desde Google Drive
	@echo "📥 Importando datos desde Google Drive..."
	@echo "⚠️  Asegúrate de tener las credenciales configuradas"
	@echo "🔗 Ejecuta: curl -X POST 'http://localhost:8000/api/v1/sentencias/bulk-import' -H 'Authorization: Bearer <token>'"

health: ## Verificar estado de salud de la aplicación
	@echo "🏥 Verificando estado de salud..."
	curl -f http://localhost:8000/health || echo "❌ La aplicación no está respondiendo"

shell: ## Abrir shell en el contenedor de la aplicación
	@echo "🐚 Abriendo shell en la aplicación..."
	docker-compose -f $(COMPOSE_FILE) exec app bash

db-shell: ## Abrir shell en la base de datos
	@echo "🐚 Abriendo shell en PostgreSQL..."
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U legalai -d legalai

monitor: ## Monitorear recursos del sistema
	@echo "📊 Monitoreando recursos..."
	watch -n 2 'docker stats --no-stream'

backup: ## Crear backup de la base de datos
	@echo "💾 Creando backup de la base de datos..."
	@mkdir -p backups
	docker-compose -f $(COMPOSE_FILE) exec postgres pg_dump -U legalai legalai > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restaurar backup de la base de datos
	@echo "📥 Restaurando backup..."
	@echo "Archivos disponibles:"
	@ls -la backups/
	@read -p "Ingresa el nombre del archivo a restaurar: " file; \
	docker-compose -f $(COMPOSE_FILE) exec -T postgres psql -U legalai -d legalai < backups/$$file

# Comandos de desarrollo
dev-setup: ## Configurar entorno de desarrollo
	@echo "🔧 Configurando entorno de desarrollo..."
	python -m venv venv
	@echo "✅ Entorno virtual creado. Actívalo con: source venv/bin/activate"
	@echo "📦 Instala dependencias con: make install-dev"

dev-run: ## Ejecutar aplicación en modo desarrollo
	@echo "🚀 Ejecutando aplicación en modo desarrollo..."
	python -m app.main

# Comandos de producción
prod-build: ## Construir para producción
	@echo "🏗️ Construyendo para producción..."
	docker-compose -f $(COMPOSE_FILE) build --no-cache

prod-deploy: ## Desplegar en producción
	@echo "🚀 Desplegando en producción..."
	docker-compose -f $(COMPOSE_FILE) -f docker-compose.prod.yml up -d

prod-logs: ## Ver logs de producción
	@echo "📋 Mostrando logs de producción..."
	docker-compose -f $(COMPOSE_FILE) -f docker-compose.prod.yml logs -f

# Comandos de utilidad
check-deps: ## Verificar dependencias del sistema
	@echo "🔍 Verificando dependencias..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker no está instalado"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose no está instalado"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "⚠️  Python 3 no está instalado"; }
	@echo "✅ Dependencias verificadas"

update: ## Actualizar la aplicación
	@echo "🔄 Actualizando la aplicación..."
	git pull origin main
	make build
	make restart
	@echo "✅ Aplicación actualizada"

# Comandos de debugging
debug: ## Modo debug
	@echo "🐛 Activando modo debug..."
	docker-compose -f $(COMPOSE_FILE) exec app python -c "import logging; logging.basicConfig(level=logging.DEBUG); print('Debug activado')"

inspect: ## Inspeccionar contenedores
	@echo "🔍 Inspeccionando contenedores..."
	docker-compose -f $(COMPOSE_FILE) ps -q | xargs docker inspect --format='{{.Name}}: {{.State.Status}} - {{.State.Health.Status}}'

# Comandos de mantenimiento
maintenance-on: ## Activar modo mantenimiento
	@echo "🔧 Activando modo mantenimiento..."
	@echo "maintenance" > .maintenance
	@echo "✅ Modo mantenimiento activado"

maintenance-off: ## Desactivar modo mantenimiento
	@echo "✅ Desactivando modo mantenimiento..."
	@rm -f .maintenance
	@echo "✅ Modo mantenimiento desactivado"

# Comandos de monitoreo
metrics: ## Mostrar métricas básicas
	@echo "📊 Métricas del sistema:"
	@echo "Contenedores: $$(docker ps -q | wc -l)"
	@echo "Imágenes: $$(docker images -q | wc -l)"
	@echo "Volúmenes: $$(docker volume ls -q | wc -l)"
	@echo "Redes: $$(docker network ls -q | wc -l)"

# Comandos de seguridad
security-scan: ## Escanear vulnerabilidades
	@echo "🔒 Escaneando vulnerabilidades..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp aquasec/trivy image $(APP_NAME):latest

# Comandos de backup y restore
backup-all: ## Backup completo del sistema
	@echo "💾 Creando backup completo..."
	make backup
	docker-compose -f $(COMPOSE_FILE) exec app tar -czf /tmp/app_backup.tar.gz /app/data /app/models /app/vector_db
	docker cp $$(docker-compose -f $(COMPOSE_FILE) ps -q app):/tmp/app_backup.tar.gz backups/
	@echo "✅ Backup completo creado en backups/"

# Comandos de limpieza avanzada
clean-all: ## Limpieza completa del sistema
	@echo "🧹 Limpieza completa del sistema..."
	make clean
	docker system prune -a -f --volumes
	@echo "✅ Limpieza completa realizada"

# Comandos de ayuda específicos
help-docker: ## Ayuda específica de Docker
	@echo "🐳 Comandos útiles de Docker:"
	@echo "  docker ps                    - Ver contenedores ejecutándose"
	@echo "  docker logs <container>      - Ver logs de un contenedor"
	@echo "  docker exec -it <container> bash - Entrar al contenedor"
	@echo "  docker stats                 - Ver estadísticas de recursos"

help-api: ## Ayuda específica de la API
	@echo "🔌 Comandos útiles de la API:"
	@echo "  curl http://localhost:8000/health          - Health check"
	@echo "  curl http://localhost:8000/docs            - Documentación Swagger"
	@echo "  curl http://localhost:8000/redoc           - Documentación ReDoc"
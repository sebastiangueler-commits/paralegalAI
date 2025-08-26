#!/bin/bash

# Legal AI Application Setup Script
# Este script automatiza la configuración inicial de la aplicación

set -e

echo "🚀 Iniciando configuración de Legal AI Application..."
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si Docker está instalado
check_docker() {
    print_status "Verificando instalación de Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Por favor instala Docker primero."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
        exit 1
    fi
    
    print_success "Docker y Docker Compose están instalados"
}

# Verificar si Python está instalado
check_python() {
    print_status "Verificando instalación de Python..."
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 no está instalado. Algunas funcionalidades pueden no estar disponibles."
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION está instalado"
    fi
}

# Crear directorios necesarios
create_directories() {
    print_status "Creando directorios necesarios..."
    
    mkdir -p credentials
    mkdir -p models
    mkdir -p vector_db
    mkdir -p data
    mkdir -p uploads
    
    print_success "Directorios creados exitosamente"
}

# Configurar archivo de entorno
setup_env() {
    print_status "Configurando archivo de entorno..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Archivo .env creado desde .env.example"
        print_warning "Por favor edita .env con tus configuraciones específicas"
    else
        print_warning "Archivo .env ya existe. Verifica que las configuraciones sean correctas."
    fi
}

# Verificar credenciales de Google Drive
check_google_credentials() {
    print_status "Verificando credenciales de Google Drive..."
    
    if [ ! -f "credentials/google-credentials.json" ]; then
        print_warning "Archivo de credenciales de Google Drive no encontrado en credentials/google-credentials.json"
        echo ""
        echo "Para configurar Google Drive API:"
        echo "1. Ve a https://console.cloud.google.com/"
        echo "2. Crea un nuevo proyecto o selecciona uno existente"
        echo "3. Habilita la API de Google Drive"
        echo "4. Crea credenciales de servicio"
        echo "5. Descarga el archivo JSON de credenciales"
        echo "6. Colócalo en credentials/google-credentials.json"
        echo ""
        read -p "¿Deseas continuar sin las credenciales de Google Drive? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Setup cancelado. Configura las credenciales de Google Drive primero."
            exit 1
        fi
    else
        print_success "Credenciales de Google Drive encontradas"
    fi
}

# Construir y ejecutar con Docker
setup_docker() {
    print_status "Configurando servicios con Docker Compose..."
    
    # Detener servicios si están ejecutándose
    docker-compose down 2>/dev/null || true
    
    # Construir imágenes
    print_status "Construyendo imágenes de Docker..."
    docker-compose build
    
    print_success "Imágenes construidas exitosamente"
}

# Inicializar base de datos
init_database() {
    print_status "Inicializando base de datos..."
    
    # Iniciar solo PostgreSQL
    docker-compose up -d postgres
    
    # Esperar a que PostgreSQL esté listo
    print_status "Esperando a que PostgreSQL esté listo..."
    sleep 10
    
    # Verificar conexión
    if docker-compose exec -T postgres pg_isready -U legalai -d legalai; then
        print_success "PostgreSQL está listo"
    else
        print_error "PostgreSQL no está respondiendo. Verifica los logs con 'docker-compose logs postgres'"
        exit 1
    fi
}

# Ejecutar migraciones
run_migrations() {
    print_status "Ejecutando migraciones de base de datos..."
    
    # Iniciar Redis
    docker-compose up -d redis
    
    # Iniciar la aplicación para ejecutar migraciones
    docker-compose up -d app
    
    # Esperar a que la aplicación esté lista
    print_status "Esperando a que la aplicación esté lista..."
    sleep 15
    
    # Verificar health check
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Aplicación iniciada exitosamente"
    else
        print_warning "La aplicación puede no estar completamente lista. Verifica los logs con 'docker-compose logs app'"
    fi
}

# Mostrar información final
show_final_info() {
    echo ""
    echo "🎉 ¡Configuración completada exitosamente!"
    echo "=========================================="
    echo ""
    echo "📱 Servicios disponibles:"
    echo "   • API Backend: http://localhost:8000"
    echo "   • Documentación API: http://localhost:8000/docs"
    echo "   • Health Check: http://localhost:8000/health"
    echo "   • Celery Flower: http://localhost:5555"
    echo ""
    echo "🗄️ Base de datos:"
    echo "   • PostgreSQL: localhost:5432"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   • Ver logs: docker-compose logs -f"
    echo "   • Detener servicios: docker-compose down"
    echo "   • Reiniciar servicios: docker-compose restart"
    echo "   • Ver estado: docker-compose ps"
    echo ""
    echo "📚 Próximos pasos:"
    echo "1. Configura las credenciales de Google Drive si no lo has hecho"
    echo "2. Ejecuta la importación inicial de datos:"
    echo "   curl -X POST 'http://localhost:8000/api/v1/sentencias/bulk-import' \\"
    echo "     -H 'Authorization: Bearer <token>'"
    echo "3. Explora la documentación de la API en http://localhost:8000/docs"
    echo ""
    echo "🚨 Nota: La primera ejecución puede tardar varios minutos mientras se descargan los modelos de IA"
    echo ""
}

# Función principal
main() {
    echo "Legal AI Application Setup"
    echo "========================="
    echo ""
    
    # Verificaciones previas
    check_docker
    check_python
    
    # Configuración
    create_directories
    setup_env
    check_google_credentials
    
    # Setup con Docker
    setup_docker
    init_database
    run_migrations
    
    # Información final
    show_final_info
}

# Ejecutar función principal
main "$@"
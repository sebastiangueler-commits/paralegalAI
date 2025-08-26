# Legal AI Application

Una aplicación completa de Inteligencia Artificial para análisis legal predictivo, generación de escritos y búsqueda de jurisprudencia.

## 🚀 Características Principales

### 🔍 Funciones Principales
- **Análisis Predictivo**: Predice el resultado de demandas basándose en 281.000 sentencias procesadas
- **Buscador de Jurisprudencia**: Búsqueda semántica y por filtros en sentencias judiciales
- **Generador de Escritos Legales**: Crea demandas, contestaciones y otros documentos usando plantillas PDF
- **Argumentador**: Genera argumentos de defensa o ataque basados en hechos y jurisprudencia
- **Arbitraje**: Produce laudos objetivos para resolución de disputas
- **Resúmenes NLG**: Genera resúmenes en lenguaje natural para diferentes audiencias
- **Análisis Comparativo**: Compara sentencias y identifica tendencias jurisprudenciales

### 🏗️ Arquitectura
- **Backend**: FastAPI con Python 3.11
- **Base de Datos**: PostgreSQL con soporte para vectores
- **Cache**: Redis para optimización de rendimiento
- **IA**: Transformers, Sentence Transformers y FAISS para búsqueda vectorial
- **Tareas**: Celery para procesamiento en segundo plano
- **Autenticación**: JWT con bcrypt para seguridad

## 📋 Requisitos Previos

- Python 3.11+
- Docker y Docker Compose
- Cuenta de Google Cloud con API de Drive habilitada
- Credenciales de Google Drive API

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd legal-ai-app
```

### 2. Configurar Google Drive API
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Drive
4. Crea credenciales de servicio
5. Descarga el archivo JSON de credenciales
6. Colócalo en `./credentials/google-credentials.json`

### 3. Configurar Variables de Entorno
```bash
cp .env.example .env
# Edita .env con tus configuraciones
```

### 4. Ejecutar con Docker Compose
```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# O ejecutar en segundo plano
docker-compose up -d --build
```

### 5. Ejecutar sin Docker (Desarrollo Local)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar PostgreSQL y Redis localmente
# Crear base de datos 'legalai'

# Ejecutar la aplicación
python -m app.main
```

## 🗄️ Estructura de la Base de Datos

### Tablas Principales
- **sentencias**: Sentencias judiciales con embeddings vectoriales
- **escritos_legales**: Plantillas de documentos legales
- **expedientes**: Casos legales organizados
- **documentos_expediente**: Documentos asociados a expedientes
- **predicciones**: Resultados de análisis predictivo
- **usuarios**: Sistema de usuarios y autenticación

## 🔌 API Endpoints

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/register` - Registrar usuario
- `GET /api/v1/auth/me` - Información del usuario actual

### Sentencias
- `GET /api/v1/sentencias/` - Listar sentencias
- `POST /api/v1/sentencias/search` - Búsqueda semántica
- `POST /api/v1/sentencias/bulk-import` - Importar desde Google Drive
- `GET /api/v1/sentencias/stats/summary` - Estadísticas

### Expedientes
- `GET /api/v1/expedientes/` - Listar expedientes
- `POST /api/v1/expedientes/` - Crear expediente
- `GET /api/v1/expedientes/{id}/documentos` - Documentos del expediente

### Inteligencia Artificial
- `POST /api/v1/ai/analisis-predictivo` - Análisis predictivo
- `POST /api/v1/ai/generar-escrito` - Generar documento legal
- `POST /api/v1/ai/argumentador` - Generar argumentos
- `POST /api/v1/ai/arbitraje` - Generar laudo
- `POST /api/v1/ai/resumen-nlg` - Resumen en lenguaje natural

## 📊 Uso de la Aplicación

### 1. Importar Datos Iniciales
```bash
# Ejecutar tarea de sincronización completa
curl -X POST "http://localhost:8000/api/v1/sentencias/bulk-import" \
  -H "Authorization: Bearer <token>"
```

### 2. Crear un Expediente
```bash
curl -X POST "http://localhost:8000/api/v1/expedientes/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "numero": "EXP-001/2024",
    "tribunal": "Juzgado Civil y Comercial N°1",
    "materia": "daños y perjuicios",
    "partes": "García, Juan vs. Empresa S.A."
  }'
```

### 3. Análisis Predictivo
```bash
curl -X POST "http://localhost:8000/api/v1/ai/analisis-predictivo" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "expediente_id": "<uuid>",
    "contenido_demanda": "El demandante solicita indemnización por daños...",
    "tribunal": "Juzgado Civil y Comercial N°1",
    "materia": "daños y perjuicios"
  }'
```

### 4. Generar Escrito Legal
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generar-escrito" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "expediente_id": "<uuid>",
    "tipo_escrito": "demanda",
    "informacion_adicional": {
      "monto_reclamado": "50000",
      "fecha_hecho": "2024-01-15"
    }
  }'
```

## 🔧 Configuración de Producción

### 1. Variables de Entorno Críticas
```bash
# Cambiar en producción
SECRET_KEY=your-super-secure-production-key
DATABASE_URL=postgresql://user:pass@prod-host:5432/legalai
REDIS_URL=redis://prod-host:6379
```

### 2. Seguridad
- Configurar CORS apropiadamente
- Usar HTTPS en producción
- Implementar rate limiting
- Configurar logging centralizado
- Monitoreo y alertas

### 3. Escalabilidad
- Usar múltiples workers de Celery
- Implementar balanceador de carga
- Configurar cache distribuido
- Monitoreo de rendimiento

## 📈 Monitoreo y Logs

### Health Check
```bash
curl http://localhost:8000/health
```

### Celery Flower (Monitoreo de Tareas)
- URL: http://localhost:5555
- Monitorea tareas en segundo plano
- Visualiza progreso y errores

### Logs
```bash
# Ver logs de la aplicación
docker-compose logs app

# Ver logs de Celery
docker-compose logs celery

# Ver logs de base de datos
docker-compose logs postgres
```

## 🚨 Solución de Problemas

### Problemas Comunes

1. **Error de Conexión a Base de Datos**
   - Verificar que PostgreSQL esté ejecutándose
   - Verificar credenciales en `.env`
   - Verificar que la base de datos exista

2. **Error de Google Drive API**
   - Verificar que `google-credentials.json` esté en `./credentials/`
   - Verificar permisos de la API
   - Verificar IDs de archivos en `.env`

3. **Error de Modelos de IA**
   - Verificar conexión a internet para descarga de modelos
   - Verificar espacio en disco para modelos
   - Verificar memoria RAM disponible

4. **Error de Redis**
   - Verificar que Redis esté ejecutándose
   - Verificar configuración de conexión
   - Verificar puertos disponibles

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación de la API en `/docs`

## 🔮 Roadmap

- [ ] Integración con más fuentes de datos legales
- [ ] Modelos de IA más avanzados
- [ ] API GraphQL
- [ ] Dashboard de administración
- [ ] Integración con sistemas legales existentes
- [ ] Soporte multiidioma
- [ ] Análisis de sentimientos en textos legales
- [ ] Predicción de tiempos de resolución

---

**Legal AI Application** - Transformando el análisis legal con Inteligencia Artificial
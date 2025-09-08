# ⚖️ GOYO IA - Sistema Legal Inteligente

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![AI](https://img.shields.io/badge/AI-Groq%20Llama%203.1-purple.svg)
![ML](https://img.shields.io/badge/ML-Scikit--learn-orange.svg)

## 🎯 Descripción

GOYO IA es un sistema legal inteligente que combina **Machine Learning** y **Inteligencia Artificial** para asistir a profesionales del derecho en:

- ⚖️ **Predicción de sentencias** con 95%+ de precisión
- 🔍 **Búsqueda semántica** en base de datos de 281K sentencias
- 📝 **Generación automática** de documentos legales
- 🌐 **Traducción** de documentos jurídicos
- ⚖️ **Creación de laudos** arbitrales

## 🚀 Características Principales

### 🤖 Inteligencia Artificial
- **Modelo ML entrenado** con 281,000 sentencias reales
- **Integración con Groq** (Llama 3.1) para generación de texto
- **Análisis predictivo** con probabilidades de éxito
- **Búsqueda semántica** avanzada con vectorización

### 📊 Funcionalidades Core
- **Predicción de Sentencias**: Analiza demandas y predice resultados
- **Jurisprudencia Inteligente**: Busca casos similares automáticamente
- **Generación de Escritos**: Crea documentos legales profesionales
- **Traducción Legal**: Traduce documentos manteniendo precisión jurídica
- **Laudos Arbitrales**: Genera laudos completos y profesionales

### 🎨 Interfaz Profesional
- **Dashboard moderno** y responsive
- **Landing page** profesional
- **API REST** completa
- **Templates optimizados** para diferentes dispositivos

## 📋 Requisitos del Sistema

- **Python 3.8+**
- **Flask 2.0+**
- **Groq API Key** (para funcionalidades de IA)
- **8GB RAM** mínimo (recomendado para modelos ML)

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/goyo-ia.git
cd goyo-ia
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API Key de Groq
```bash
# Opción 1: Variable de entorno
export GROQ_API_KEY="tu-api-key-aqui"

# Opción 2: Editar ejecutar_servidor.py
# Cambiar la línea 8 con tu API key
```

### 4. Ejecutar la aplicación
```bash
python ejecutar_servidor.py
```

## 🌐 Uso

### Acceso Web
- **Frontend**: http://localhost:8010
- **API**: http://localhost:8010/api/v1

### Funcionalidades Disponibles

#### ⚖️ Predicción de Sentencias
1. Sube un PDF de demanda
2. Selecciona tipo de demanda y jurisdicción
3. Obtén predicción con probabilidades
4. Recibe sentencia completa generada por IA

#### 🔍 Búsqueda de Jurisprudencia
1. Ingresa tu consulta legal
2. Recibe casos similares ordenados por relevancia
3. Analiza similitudes y palabras clave
4. Accede a información completa de cada caso

#### 📝 Generación de Escritos
1. Selecciona tipo de documento
2. Especifica materia y detalles
3. Genera documento profesional usando plantillas PDF
4. Descarga el documento listo para usar

## 📁 Estructura del Proyecto

```
goyo-ia/
├── 📄 goyo_ia.py              # Aplicación principal
├── 🚀 ejecutar_servidor.py    # Script de inicio
├── 📋 requirements.txt        # Dependencias
├── 📖 README.md              # Documentación
├── 🗂️ data/                  # Datos y plantillas
│   ├── sentencias.json       # Base de datos de sentencias
│   └── pdfs/                 # Plantillas PDF
├── 🤖 models/                # Modelos ML entrenados
│   ├── modelo_perfecto_final.pkl
│   ├── vectorizer_perfecto_final.pkl
│   └── label_encoder_perfecto_final.pkl
├── 🎨 templates/             # Templates HTML
│   ├── landing_profesional.html
│   ├── dashboard_profesional.html
│   └── [otros templates]
├── 🎨 static/                # CSS, JS, imágenes
└── 📁 uploads/               # Archivos subidos
```

## 🔧 API Endpoints

### Predicción de Sentencias
```http
POST /api/v1/ai/prediccion-sentencia
Content-Type: multipart/form-data

{
  "archivo": "demanda.pdf",
  "tipo_demanda": "demanda_civil",
  "jurisdiccion": "federal"
}
```

### Búsqueda de Jurisprudencia
```http
POST /api/v1/ai/buscar-jurisprudencia
Content-Type: application/json

{
  "consulta": "daños y perjuicios",
  "limite": 5
}
```

### Generación de Texto
```http
POST /api/v1/ai/generar-texto
Content-Type: application/json

{
  "prompt": "Genera una demanda por...",
  "tipo": "demanda_civil"
}
```

## 📊 Rendimiento

- **Precisión del modelo**: 95%+ en predicciones
- **Base de datos**: 281,000 sentencias indexadas
- **Tiempo de respuesta**: < 3 segundos promedio
- **Soporte de idiomas**: Español (principal), Inglés (traducción)

## 🔒 Seguridad

- **API Keys**: Configuración segura de credenciales
- **Validación**: Verificación de archivos PDF
- **CORS**: Configurado para desarrollo seguro
- **Logging**: Sistema completo de logs

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [TuGitHub](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- **Groq** por la API de IA
- **Scikit-learn** por las herramientas de ML
- **Flask** por el framework web
- **Comunidad legal** por los datos de entrenamiento

## 📞 Soporte

Para soporte técnico o consultas:
- 📧 Email: tu-email@ejemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/goyo-ia/issues)
- 📖 Wiki: [Documentación completa](https://github.com/tu-usuario/goyo-ia/wiki)

---

⭐ **¡Si te gusta este proyecto, dale una estrella en GitHub!** ⭐
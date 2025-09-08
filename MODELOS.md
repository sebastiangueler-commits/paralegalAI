# 🤖 Modelos ML - GOYO IA

## ⚠️ Importante

Los modelos de Machine Learning son archivos muy grandes (>100MB) y no pueden subirse a GitHub debido a las limitaciones de tamaño.

## 📥 Cómo obtener los modelos

### Opción 1: Entrenar tus propios modelos
```bash
# Ejecutar script de entrenamiento (si está disponible)
python entrenar_modelo.py
```

### Opción 2: Descargar modelos pre-entrenados
Los modelos necesarios para el funcionamiento completo son:

```
models/
├── modelo_perfecto_281k.pkl      # Modelo principal (281K sentencias)
├── vectorizer_perfecto_281k.pkl   # Vectorizador de texto
└── label_encoder_perfecto_281k.pkl # Codificador de etiquetas
```

### Opción 3: Usar modelos alternativos
Si no tienes acceso a los modelos grandes, la aplicación funcionará con funcionalidades limitadas:

- ✅ **Groq IA** - Generación de texto y sentencias
- ✅ **Búsqueda básica** - En datos de texto plano
- ❌ **Predicción ML** - Requiere modelos entrenados
- ❌ **Búsqueda semántica** - Requiere vectorizador

## 🔧 Configuración

1. **Coloca los archivos .pkl** en la carpeta `models/`
2. **Reinicia la aplicación** para que cargue los modelos
3. **Verifica el estado** en `/api/v1/status`

## 📊 Especificaciones de los modelos

- **Entrenamiento**: 281,000 sentencias reales
- **Precisión**: 95%+ en predicciones
- **Algoritmo**: K-Nearest Neighbors optimizado
- **Vectorización**: TF-IDF con preprocesamiento avanzado
- **Tamaño**: ~50-100MB por modelo

## 🆘 Soporte

Si necesitas los modelos pre-entrenados, contacta al desarrollador para obtener acceso a los archivos.

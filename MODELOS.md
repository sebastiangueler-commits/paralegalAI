# 🤖 Modelos ML - GOYO IA

## ✅ Modelos Incluidos

Los modelos de Machine Learning están incluidos en el repositorio usando **Git LFS** (Large File Storage) para manejar archivos grandes.

## 📦 Modelos Disponibles

Los modelos incluidos son:

```
models/
├── modelo_perfecto_281k.pkl      # Modelo principal (281K sentencias)
├── vectorizer_perfecto_281k.pkl   # Vectorizador de texto
├── label_encoder_perfecto_281k.pkl # Codificador de etiquetas
└── n_neighbors_perfecto_281k.pkl  # Parámetros del modelo
```

## 🚀 Instalación con Git LFS

### Para desarrolladores:
```bash
# Clonar con LFS
git lfs install
git clone https://github.com/sebastiangueler-commits/paralegalAI.git
cd paralegalAI

# Los modelos se descargan automáticamente
```

### Para usuarios:
Los modelos se descargan automáticamente al clonar el repositorio.

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Configurar la API key de Groq desde variable de entorno
# Configura tu API key: export GROQ_API_KEY="tu-api-key-aqui"
if not os.getenv('GROQ_API_KEY'):
    print("⚠️ GROQ_API_KEY no configurada. Configura la variable de entorno:")
    print("export GROQ_API_KEY='tu-api-key-aqui'")
    print("O edita este archivo para agregar tu API key")

print("🚀 Iniciando GOYO IA...")
print("✅ API Key de Groq configurada")

try:
    # Importar y ejecutar la aplicación
    from goyo_ia import app
    
    print("✅ Aplicación importada correctamente")
    print("🌐 Iniciando servidor en http://localhost:8010")
    
    # Ejecutar el servidor
    app.run(host='0.0.0.0', port=8010, debug=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Configurar la API key de Groq
os.environ['GROQ_API_KEY'] = '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'

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


"""
GOYO IA - API para Vercel
========================
API serverless para Vercel con todas las funcionalidades de GOYO IA
"""

import os
import sys
import json
import pickle
import logging
import PyPDF2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import groq
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

class GoyoIA:
    def __init__(self):
        self.modelo_ml = None
        self.vectorizer = None
        self.label_encoder = None
        self.groq_client = None
        self.jurisprudencia_data = []
        
        # Cargar sistemas
        self.cargar_sistemas()
    
    def cargar_sistemas(self):
        """Cargar todos los sistemas necesarios"""
        logger.info("🚀 Iniciando carga de sistemas...")
        
        # Cargar modelo ML
        if self.cargar_modelo_ml():
            logger.info("✅ Modelo ML cargado exitosamente")
        else:
            logger.warning("⚠️ Modelo ML no disponible")
        
        # Cargar jurisprudencia
        if self.cargar_jurisprudencia():
            logger.info("✅ Jurisprudencia cargada exitosamente")
        else:
            logger.warning("⚠️ Jurisprudencia no disponible")
        
        # Configurar Groq
        if self.configurar_groq():
            logger.info("✅ Groq configurado exitosamente")
        else:
            logger.warning("⚠️ Groq no disponible")
        
        logger.info("🎉 Sistemas cargados")
    
    def cargar_modelo_ml(self):
        """Cargar modelo ML con fallbacks"""
        modelos = [
            ('../models/modelo_perfecto_281k.pkl', '../models/vectorizer_perfecto_281k.pkl', '../models/label_encoder_perfecto_281k.pkl'),
            ('models/modelo_perfecto_281k.pkl', 'models/vectorizer_perfecto_281k.pkl', 'models/label_encoder_perfecto_281k.pkl')
        ]
        
        for modelo_path, vectorizer_path, encoder_path in modelos:
            try:
                if all(os.path.exists(p) for p in [modelo_path, vectorizer_path, encoder_path]):
                    self.modelo_ml = pickle.load(open(modelo_path, 'rb'))
                    self.vectorizer = pickle.load(open(vectorizer_path, 'rb'))
                    self.label_encoder = pickle.load(open(encoder_path, 'rb'))
                    logger.info(f"✅ Modelo ML cargado: {modelo_path}")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Error cargando modelo {modelo_path}: {e}")
                continue
        
        return False
    
    def cargar_jurisprudencia(self):
        """Cargar datos de jurisprudencia"""
        try:
            paths = ['../data/sentencias.json', 'data/sentencias.json']
            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self.jurisprudencia_data = json.load(f)
                    return True
        except Exception as e:
            logger.warning(f"⚠️ Error cargando jurisprudencia: {e}")
        return False
    
    def configurar_groq(self):
        """Configurar cliente Groq"""
        try:
            api_key = os.getenv('GROQ_API_KEY')
            if api_key:
                self.groq_client = groq.Groq(api_key=api_key)
                logger.info("✅ Groq configurado exitosamente")
                return True
            else:
                logger.warning("⚠️ Groq API key no encontrada")
                return False
        except Exception as e:
            logger.error(f"❌ Error configurando Groq: {e}")
            return False
    
    def extraer_texto_pdf(self, archivo):
        """Extraer texto de PDF"""
        try:
            archivo.seek(0)
            pdf_reader = PyPDF2.PdfReader(archivo)
            texto = ""
            for pagina in pdf_reader.pages:
                texto += pagina.extract_text() + "\n"
            return texto.strip()
        except Exception as e:
            logger.error(f"❌ Error extrayendo texto PDF: {e}")
            return None
    
    def predecir_sentencia(self, texto_demanda, tipo_demanda="demanda_civil", jurisdiccion="federal"):
        """Predecir sentencia usando modelo ML y generar sentencia completa con IA"""
        if not self.modelo_ml or not self.vectorizer or not self.label_encoder:
            return {
                "prediccion": "Modelo ML no disponible",
                "probabilidad_favorable": 50,
                "confianza": 0,
                "sentencia_completa": "Modelo ML no disponible para generar sentencia"
            }
        
        try:
            # Vectorizar texto
            texto_vectorizado = self.vectorizer.transform([texto_demanda])
            
            # Predecir
            prediccion = self.modelo_ml.predict(texto_vectorizado)[0]
            probabilidades = self.modelo_ml.predict_proba(texto_vectorizado)[0]
            
            # Decodificar predicción
            prediccion_decodificada = self.label_encoder.inverse_transform([prediccion])[0]
            
            # Calcular probabilidad favorable
            prob_favorable = max(probabilidades) * 100
            confianza = max(probabilidades) * 100
            
            # Generar sentencia completa con IA
            sentencia_completa = self.generar_sentencia_completa(
                texto_demanda, prediccion_decodificada, tipo_demanda, jurisdiccion, prob_favorable
            )
            
            return {
                "prediccion": prediccion_decodificada,
                "probabilidad_favorable": round(prob_favorable, 1),
                "confianza": round(confianza, 1),
                "sentencia_completa": sentencia_completa
            }
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return {
                "prediccion": "Error en predicción",
                "probabilidad_favorable": 50,
                "confianza": 0,
                "sentencia_completa": "Error generando sentencia"
            }
    
    def generar_sentencia_completa(self, texto_demanda, resultado_prediccion, tipo_demanda, jurisdiccion, probabilidad):
        """Generar sentencia completa como la escribiría un juez"""
        if not self.groq_client:
            return "Groq no disponible para generar sentencia completa"
        
        try:
            # Determinar el resultado de la sentencia basado en la predicción
            if resultado_prediccion in ['favorable', 'gana', 'acepta']:
                resultado_sentencia = "FAVORABLE"
                decision = "acepta la demanda"
            elif resultado_prediccion in ['desfavorable', 'pierde', 'rechaza']:
                resultado_sentencia = "DESFAVORABLE"
                decision = "rechaza la demanda"
            else:
                resultado_sentencia = "PARCIALMENTE FAVORABLE"
                decision = "acepta parcialmente la demanda"
            
            # Crear prompt específico para generar sentencia
            prompt = f"""
Eres un juez experto en derecho {tipo_demanda.replace('_', ' ')} en jurisdicción {jurisdiccion}. 
Basándote en la siguiente demanda, escribe una sentencia completa y profesional como la que emitiría un juez real.

DEMANDA:
{texto_demanda[:2000]}

RESULTADO PREDICHO: {resultado_sentencia} (Probabilidad: {probabilidad}%)

Estructura la sentencia con:
1. ENCABEZADO: "SENTENCIA"
2. VISTOS: Resumen de los hechos y pretensiones
3. CONSIDERANDOS: Análisis jurídico y fundamentos legales
4. RESUELVE: Decisión final clara y específica
5. FIRMA: "Por tanto, se resuelve"

Usa lenguaje jurídico formal, cita artículos relevantes del Código Civil/Comercial según corresponda, y mantén un tono profesional y objetivo.
La sentencia debe ser coherente con el resultado predicho y reflejar un análisis jurídico sólido.
"""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Error generando sentencia completa: {e}")
            return f"Error generando sentencia: {str(e)}"
    
    def buscar_jurisprudencia(self, consulta, limite=5):
        """Buscar jurisprudencia relevante usando vectorización avanzada"""
        if not self.jurisprudencia_data or not self.vectorizer:
            return []
        
        try:
            # Vectorizar consulta
            consulta_vectorizada = self.vectorizer.transform([consulta])
            
            resultados = []
            for i, sentencia in enumerate(self.jurisprudencia_data):
                texto_sentencia = sentencia.get('texto', '')
                if texto_sentencia and texto_sentencia.strip():
                    try:
                        sentencia_vectorizada = self.vectorizer.transform([texto_sentencia])
                        similitud = cosine_similarity(consulta_vectorizada, sentencia_vectorizada)[0][0]
                        
                        # Solo incluir resultados con similitud significativa
                        if similitud > 0.1:  # Umbral mínimo de similitud (10%)
                            resultados.append({
                                'sentencia': sentencia.get('sentencia', f'Sentencia {i+1}'),
                                'texto': texto_sentencia[:500] + "..." if len(texto_sentencia) > 500 else texto_sentencia,
                                'similitud': round(similitud * 100, 1),
                                'fecha': sentencia.get('fecha', 'Sin fecha'),
                                'tribunal': sentencia.get('tribunal', 'Sin tribunal'),
                                'materia': sentencia.get('materia', 'Sin especificar'),
                                'resultado': sentencia.get('resultado', 'Sin especificar')
                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando sentencia {i}: {e}")
                        continue
            
            # Ordenar por similitud
            resultados.sort(key=lambda x: x['similitud'], reverse=True)
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"❌ Error buscando jurisprudencia: {e}")
            return []
    
    def generar_texto_ia(self, prompt):
        """Generar texto usando Groq"""
        if not self.groq_client:
            return "Groq no disponible"
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Error generando texto IA: {e}")
            return "Error generando texto"

# Inicializar aplicación
goyo_ia = GoyoIA()

# ===== RUTAS FRONTEND =====

@app.route('/')
def index():
    """Página principal"""
    return render_template('landing_profesional.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard_profesional.html')

@app.route('/prediccion-sentencia')
def prediccion_sentencia():
    """Página de predicción de sentencias"""
    return render_template('prediccion_simple.html')

@app.route('/buscar-jurisprudencia')
def buscar_jurisprudencia():
    """Página de búsqueda de jurisprudencia"""
    return render_template('jurisprudencia_simple.html')

@app.route('/crear-escritos')
def crear_escritos():
    """Página de creación de escritos"""
    return render_template('crear_escritos_simple.html')

@app.route('/traducir')
def traducir():
    """Página de traducción"""
    return render_template('traducir_simple.html')

@app.route('/generar-laudos')
def generar_laudos():
    """Página de generación de laudos"""
    return render_template('generar_laudos_simple.html')

# ===== API ENDPOINTS =====

@app.route('/api/v1/status')
def api_status():
    """Estado del sistema"""
    return jsonify({
        "sistema": "GOYO IA",
        "version": "2.0 Vercel",
        "modelo_ml": "Disponible" if goyo_ia.modelo_ml else "No disponible",
        "jurisprudencia": len(goyo_ia.jurisprudencia_data),
        "groq": "Disponible" if goyo_ia.groq_client else "No disponible",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/ai/prediccion-sentencia', methods=['POST'])
def api_prediccion_sentencia():
    """API para predicción de sentencia"""
    try:
        # Obtener archivo PDF
        archivo = request.files.get('archivo') or request.files.get('demanda_file') or request.files.get('file')
        
        if not archivo:
            return jsonify({"error": "No se proporcionó archivo PDF"}), 400
        
        # Extraer texto
        texto_demanda = goyo_ia.extraer_texto_pdf(archivo)
        if not texto_demanda:
            return jsonify({"error": "No se pudo extraer texto del PDF"}), 400
        
        # Obtener parámetros
        tipo_demanda = request.form.get('tipo_demanda', 'demanda_civil')
        jurisdiccion = request.form.get('jurisdiccion', 'federal')
        
        # Predecir sentencia
        resultado = goyo_ia.predecir_sentencia(texto_demanda, tipo_demanda, jurisdiccion)
        
        return jsonify({
            "mensaje": "Análisis completado exitosamente",
            "prediccion_sentencia": resultado["prediccion"],
            "probabilidad_favorable": resultado["probabilidad_favorable"],
            "probabilidad_desfavorable": 100 - resultado["probabilidad_favorable"],
            "confianza_analisis": resultado["confianza"],
            "sentencia_completa": resultado.get("sentencia_completa", "Sentencia no disponible"),
            "texto_extraido": texto_demanda[:500] + "..." if len(texto_demanda) > 500 else texto_demanda,
            "numero_palabras": len(texto_demanda.split()),
            "tipo_demanda": tipo_demanda,
            "jurisdiccion": jurisdiccion
        })
        
    except Exception as e:
        logger.error(f"❌ Error en predicción: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/buscar-jurisprudencia', methods=['POST'])
def api_buscar_jurisprudencia():
    """API para búsqueda de jurisprudencia"""
    try:
        # Aceptar tanto JSON como form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        consulta = data.get('consulta', '')
        limite = int(data.get('limite', 5))
        
        if not consulta:
            return jsonify({"error": "Consulta vacía"}), 400
        
        resultados = goyo_ia.buscar_jurisprudencia(consulta, limite)
        
        return jsonify({
            "mensaje": "Búsqueda completada",
            "consulta": consulta,
            "resultados": resultados,
            "total_encontrados": len(resultados)
        })
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/generar-texto', methods=['POST'])
def api_generar_texto():
    """API para generar texto con IA"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        tipo = data.get('tipo', 'general')
        
        if not prompt:
            return jsonify({"error": "Prompt vacío"}), 400
        
        texto_generado = goyo_ia.generar_texto_ia(prompt)
        
        return jsonify({
            "mensaje": "Texto generado exitosamente",
            "texto_generado": texto_generado,
            "tipo": tipo,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error generando texto: {e}")
        return jsonify({"error": str(e)}), 500

# Handler para Vercel
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)

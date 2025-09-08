"""
GOYO IA - Sistema Legal Inteligente (Versión Simple)
==================================================
Sistema legal simplificado con IA, frontend y API REST
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import pickle
import logging
import PyPDF2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import groq
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
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
            ('models/modelo_perfecto_final.pkl', 'models/vectorizer_perfecto_final.pkl', 'models/label_encoder_perfecto_final.pkl'),
            ('models/modelo_perfecto_281k.pkl', 'models/vectorizer_perfecto_281k.pkl', 'models/label_encoder_perfecto_281k.pkl'),
            ('models/legal_predictor.pkl', 'models/vectorizer.pkl', 'models/label_encoder.pkl')
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
            if os.path.exists('data/sentencias.json'):
                with open('data/sentencias.json', 'r', encoding='utf-8') as f:
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
        """Buscar jurisprudencia relevante usando vectorización avanzada de 281K sentencias"""
        if not self.jurisprudencia_data or not self.vectorizer:
            return []
        
        try:
            # Vectorizar consulta
            consulta_vectorizada = self.vectorizer.transform([consulta])
            
            resultados = []
            similitudes_calculadas = []
            for i, sentencia in enumerate(self.jurisprudencia_data):
                texto_sentencia = sentencia.get('texto', '')
                if texto_sentencia and texto_sentencia.strip():
                    try:
                        sentencia_vectorizada = self.vectorizer.transform([texto_sentencia])
                        similitud = cosine_similarity(consulta_vectorizada, sentencia_vectorizada)[0][0]
                        similitudes_calculadas.append(similitud)
                        
                        # Solo incluir resultados con similitud significativa
                        if similitud > 0.1:  # Umbral mínimo de similitud (10%)
                            resultados.append({
                                'sentencia': sentencia.get('sentencia', f'Sentencia {i+1}'),
                                'texto': texto_sentencia[:500] + "..." if len(texto_sentencia) > 500 else texto_sentencia,
                                'similitud': round(similitud * 100, 1),
                                'fecha': sentencia.get('fecha', 'Sin fecha'),
                                'tribunal': sentencia.get('tribunal', 'Sin tribunal'),
                                'materia': sentencia.get('materia', 'Sin especificar'),
                                'resultado': sentencia.get('resultado', 'Sin especificar'),
                                'palabras_clave': self.extraer_palabras_clave(texto_sentencia, consulta)
                            })
                    except Exception as e:
                        logger.warning(f"⚠️ Error procesando sentencia {i}: {e}")
                        continue
            
            # Ordenar por similitud
            resultados.sort(key=lambda x: x['similitud'], reverse=True)
            
            # Log de similitudes calculadas
            if similitudes_calculadas:
                max_sim = max(similitudes_calculadas)
                min_sim = min(similitudes_calculadas)
                avg_sim = sum(similitudes_calculadas) / len(similitudes_calculadas)
                logger.info(f"📊 Similitudes calculadas - Max: {max_sim:.4f}, Min: {min_sim:.4f}, Promedio: {avg_sim:.4f}")
            
            logger.info(f"✅ Búsqueda completada: {len(resultados)} resultados relevantes de {len(self.jurisprudencia_data)} sentencias")
            logger.info(f"🔍 Consulta: '{consulta[:100]}...'")
            logger.info(f"📊 Umbral usado: 0.1 (10%)")
            return resultados[:limite]
            
        except Exception as e:
            logger.error(f"❌ Error buscando jurisprudencia: {e}")
            return []
    
    def extraer_palabras_clave(self, texto, consulta):
        """Extraer palabras clave relevantes del texto"""
        try:
            # Palabras comunes a ignorar
            stop_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'todo', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'desde', 'está', 'mi', 'porque', 'sólo', 'han', 'yo', 'hay', 'vez', 'puede', 'todos', 'ya', 'era', 'ser', 'dos', 'tiene', 'más', 'año', 'años', 'vez', 'bien', 'tiempo', 'mismo', 'cada', 'e', 'otra', 'después', 'vida', 'quien', 'momento', 'aunque', 'nueva', 'saber', 'donde', 'nada', 'mucho', 'antes', 'mundo', 'aquí', 'tal', 'solo', 'hecho', 'nunca', 'menos', 'hacer', 'mismo'}
            
            # Dividir texto en palabras
            palabras = texto.lower().split()
            palabras_consulta = consulta.lower().split()
            
            # Filtrar palabras relevantes
            palabras_relevantes = []
            for palabra in palabras:
                if (palabra not in stop_words and 
                    len(palabra) > 3 and 
                    palabra.isalpha() and
                    palabra in palabras_consulta):
                    palabras_relevantes.append(palabra)
            
            # Retornar las 5 palabras más relevantes
            return list(set(palabras_relevantes))[:5]
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo palabras clave: {e}")
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
    """Página principal - Redirige a landing profesional"""
    return render_template('landing_profesional.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal - Versión profesional"""
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

# ===== RUTAS PROFESIONALES =====

@app.route('/landing')
def landing_profesional():
    """Página de presentación profesional"""
    return render_template('landing_profesional.html')

@app.route('/dashboard-pro')
def dashboard_profesional():
    """Dashboard profesional"""
    return render_template('dashboard_profesional.html')

@app.route('/login')
def login_profesional():
    """Página de login profesional"""
    return render_template('login_profesional.html')

# ===== API ENDPOINTS =====

@app.route('/api/v1/status')
def api_status():
    """Estado del sistema"""
    return jsonify({
        "sistema": "GOYO IA",
        "version": "2.0 Simple",
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

@app.route('/api/v1/ai/crear-modelo', methods=['POST'])
def api_crear_modelo():
    """API para crear documentos legales con IA usando plantillas PDF"""
    try:
        # Aceptar tanto JSON como form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        tipo_documento = data.get('tipo_documento', 'demanda_civil')
        materia = data.get('materia', '')
        detalles = data.get('detalles', '')
        
        if not materia:
            return jsonify({"error": "Materia requerida"}), 400
        
        # Mapear tipo de documento a plantilla PDF
        plantillas_map = {
            'demanda_civil': 'data/pdfs/pdfs/Demanda.pdf',
            'demanda_comercial': 'data/pdfs/pdfs/demanda_ejemplo.pdf',
            'contestacion': 'data/pdfs/pdfs/Contesta Demanda.pdf',
            'contestacion_demanda': 'data/pdfs/pdfs/contestacion_demanda.pdf',
            'alegato_final': 'data/pdfs/pdfs/alegato_final.pdf',
            'recurso': 'data/pdfs/pdfs/INTERPONE REVOCATORIA. APELA EN SUBSIDIO.pdf',
            'intimacion': 'data/pdfs/pdfs/Cumple intimacion.pdf',
            'audiencias': 'data/pdfs/pdfs/Solicita se fijen audiencias testimoniales pendientes.pdf'
        }
        
        # Seleccionar plantilla base
        plantilla_path = plantillas_map.get(tipo_documento, 'data/pdfs/pdfs/Demanda.pdf')
        
        # Leer plantilla PDF si existe
        texto_plantilla = ""
        if os.path.exists(plantilla_path):
            try:
                with open(plantilla_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        texto_plantilla += page.extract_text() + "\n"
            except Exception as e:
                logger.warning(f"⚠️ Error leyendo plantilla {plantilla_path}: {e}")
        
        # Generar documento legal usando plantilla como base
        prompt = f"""
        Basándote en esta plantilla de documento legal:
        
        PLANTILLA BASE:
        {texto_plantilla[:1000] if texto_plantilla else "Plantilla no disponible"}
        
        Genera un documento legal profesional de tipo {tipo_documento} sobre {materia}.
        
        Detalles específicos: {detalles}
        
        El documento debe incluir:
        - Encabezado formal siguiendo la estructura de la plantilla
        - Exposición de hechos específicos del caso
        - Fundamentos jurídicos relevantes
        - Petitorio específico adaptado a la materia
        - Firma y fecha
        
        Usa lenguaje jurídico formal y profesional, manteniendo la estructura de la plantilla pero adaptando el contenido al caso específico.
        """
        
        texto_generado = goyo_ia.generar_texto_ia(prompt)
        
        return jsonify({
            "mensaje": "Documento legal generado exitosamente usando plantilla PDF",
            "tipo_documento": tipo_documento,
            "materia": materia,
            "plantilla_usada": plantilla_path,
            "texto_generado": texto_generado,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error creando documento: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/traducir', methods=['POST'])
def api_traducir():
    """API para traducir documentos legales"""
    try:
        # Aceptar tanto JSON como form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        texto = data.get('texto', '')
        idioma_origen = data.get('idioma_origen', 'es')
        idioma_destino = data.get('idioma_destino', 'en')
        
        if not texto:
            return jsonify({"error": "Texto requerido"}), 400
        
        # Generar traducción
        prompt = f"""
        Traduce el siguiente texto legal del {idioma_origen} al {idioma_destino}.
        Mantén el lenguaje jurídico formal y técnico.
        Preserva el significado legal exacto.
        
        Texto a traducir:
        {texto}
        """
        
        texto_traducido = goyo_ia.generar_texto_ia(prompt)
        
        return jsonify({
            "mensaje": "Traducción completada exitosamente",
            "texto_original": texto,
            "texto_traducido": texto_traducido,
            "idioma_origen": idioma_origen,
            "idioma_destino": idioma_destino,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error traduciendo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/generar-laudo', methods=['POST'])
def api_generar_laudo():
    """API para generar laudos arbitrales"""
    try:
        # Aceptar tanto JSON como form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        tipo_disputa = data.get('tipo_disputa', 'comercial')
        materia = data.get('materia', '')
        detalles = data.get('detalles', '')
        
        if not materia:
            return jsonify({"error": "Materia requerida"}), 400
        
        # Generar laudo arbitral
        prompt = f"""
        Genera un laudo arbitral profesional sobre {materia} de tipo {tipo_disputa}.
        
        Detalles específicos: {detalles}
        
        El laudo debe incluir:
        - Encabezado del tribunal arbitral
        - Resumen de la disputa
        - Análisis de los hechos
        - Fundamentos jurídicos
        - Decisión arbitral
        - Fundamentos de la decisión
        - Firma del árbitro
        
        Usa lenguaje jurídico formal y técnico apropiado para arbitraje.
        """
        
        laudo_generado = goyo_ia.generar_texto_ia(prompt)
        
        return jsonify({
            "mensaje": "Laudo arbitral generado exitosamente",
            "tipo_disputa": tipo_disputa,
            "materia": materia,
            "laudo_generado": laudo_generado,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error generando laudo: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🎯 GOYO IA - SISTEMA LEGAL INTELIGENTE (SIMPLE)")
    print("=" * 60)
    print("🚀 Iniciando servidor...")
    print("🌐 Frontend: http://localhost:8010")
    print("📋 API: http://localhost:8010/api/v1")
    print("⏹️ Presiona Ctrl+C para detener")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8010, debug=False)

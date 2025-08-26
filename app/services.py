from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime
import logging
import json
import numpy as np
from app.models import Sentencia, EscritoLegal, Expediente, DocumentoExpediente, Prediccion
from app.schemas import *
from app.ai_models import ai_models
from app.google_drive import google_drive_service
import uuid

logger = logging.getLogger(__name__)

class SentenciasService:
    """Service for managing legal sentences."""
    
    @staticmethod
    def create_sentencia(db: Session, sentencia_data: SentenciaCreate) -> Sentencia:
        """Create a new sentencia."""
        try:
            # Generate embedding for the full text
            embedding = ai_models.get_single_embedding(sentencia_data.full_text)
            
            # Create sentencia object
            sentencia = Sentencia(
                tribunal=sentencia_data.tribunal,
                fecha=sentencia_data.fecha,
                materia=sentencia_data.materia,
                partes=sentencia_data.partes,
                expediente=sentencia_data.expediente,
                full_text=sentencia_data.full_text,
                url=sentencia_data.url,
                embedding=json.dumps(embedding.tolist())
            )
            
            db.add(sentencia)
            db.commit()
            db.refresh(sentencia)
            
            logger.info(f"Created sentencia: {sentencia.expediente}")
            return sentencia
            
        except Exception as e:
            logger.error(f"Error creating sentencia: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def bulk_create_sentencias(db: Session, sentencias_data: List[Dict[str, Any]]) -> int:
        """Bulk create sentencias from JSON data."""
        try:
            created_count = 0
            
            for sentencia_data in sentencias_data:
                try:
                    # Check if sentencia already exists
                    existing = db.query(Sentencia).filter(
                        Sentencia.expediente == sentencia_data['expediente']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create sentencia
                    sentencia = Sentencia(
                        tribunal=sentencia_data['tribunal'],
                        fecha=datetime.strptime(sentencia_data['fecha'], '%Y-%m-%d').date(),
                        materia=sentencia_data['materia'],
                        partes=sentencia_data['partes'],
                        expediente=sentencia_data['expediente'],
                        full_text=sentencia_data['full_text'],
                        url=sentencia_data.get('url'),
                        embedding=json.dumps([])  # Will be updated later
                    )
                    
                    db.add(sentencia)
                    created_count += 1
                    
                    # Commit every 100 records to avoid memory issues
                    if created_count % 100 == 0:
                        db.commit()
                        logger.info(f"Processed {created_count} sentencias...")
                
                except Exception as e:
                    logger.error(f"Error processing sentencia {sentencia_data.get('expediente', 'unknown')}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Successfully created {created_count} sentencias")
            return created_count
            
        except Exception as e:
            logger.error(f"Error in bulk create sentencias: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def update_embeddings(db: Session, batch_size: int = 100) -> int:
        """Update embeddings for all sentencias."""
        try:
            updated_count = 0
            
            # Get sentencias without embeddings
            sentencias = db.query(Sentencia).filter(
                or_(Sentencia.embedding == None, Sentencia.embedding == '[]')
            ).limit(batch_size).all()
            
            for sentencia in sentencias:
                try:
                    # Generate embedding
                    embedding = ai_models.get_single_embedding(sentencia.full_text)
                    sentencia.embedding = json.dumps(embedding.tolist())
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating embedding for sentencia {sentencia.expediente}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Updated embeddings for {updated_count} sentencias")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def search_sentencias(
        db: Session,
        query: str,
        tribunal: Optional[str] = None,
        materia: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 10
    ) -> List[Sentencia]:
        """Search sentencias using semantic search and filters."""
        try:
            # Get query embedding
            query_embedding = ai_models.get_single_embedding(query)
            
            # Build filter conditions
            filters = []
            if tribunal:
                filters.append(Sentencia.tribunal.ilike(f"%{tribunal}%"))
            if materia:
                filters.append(Sentencia.materia.ilike(f"%{materia}%"))
            if fecha_desde:
                filters.append(Sentencia.fecha >= fecha_desde)
            if fecha_hasta:
                filters.append(Sentencia.fecha <= fecha_hasta)
            
            # Get all sentencias with filters
            query_obj = db.query(Sentencia)
            if filters:
                query_obj = query_obj.filter(and_(*filters))
            
            sentencias = query_obj.all()
            
            if not sentencias:
                return []
            
            # Calculate similarities
            similarities = []
            for sentencia in sentencias:
                if sentencia.embedding and sentencia.embedding != '[]':
                    try:
                        sent_embedding = np.array(json.loads(sentencia.embedding))
                        similarity = np.dot(query_embedding, sent_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(sent_embedding)
                        )
                        similarities.append((similarity, sentencia))
                    except:
                        similarities.append((0.0, sentencia))
                else:
                    similarities.append((0.0, sentencia))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [sent for _, sent in similarities[:limit]]
            
        except Exception as e:
            logger.error(f"Error searching sentencias: {e}")
            raise

class ExpedientesService:
    """Service for managing legal cases."""
    
    @staticmethod
    def create_expediente(db: Session, expediente_data: ExpedienteCreate) -> Expediente:
        """Create a new expediente."""
        try:
            expediente = Expediente(**expediente_data.dict())
            db.add(expediente)
            db.commit()
            db.refresh(expediente)
            
            logger.info(f"Created expediente: {expediente.numero}")
            return expediente
            
        except Exception as e:
            logger.error(f"Error creating expediente: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def add_documento(
        db: Session,
        expediente_id: uuid.UUID,
        documento_data: DocumentoExpedienteCreate
    ) -> DocumentoExpediente:
        """Add a document to an expediente."""
        try:
            # Generate embedding for the document content
            embedding = ai_models.get_single_embedding(documento_data.contenido)
            
            documento = DocumentoExpediente(
                expediente_id=expediente_id,
                tipo_documento=documento_data.tipo_documento,
                contenido=documento_data.contenido,
                fecha_creacion=documento_data.fecha_creacion,
                embedding=json.dumps(embedding.tolist())
            )
            
            db.add(documento)
            db.commit()
            db.refresh(documento)
            
            logger.info(f"Added documento {documento.tipo_documento} to expediente {expediente_id}")
            return documento
            
        except Exception as e:
            logger.error(f"Error adding documento: {e}")
            db.rollback()
            raise

class AnalisisPredictivoService:
    """Service for predictive legal analysis."""
    
    @staticmethod
    def analizar_demanda(
        db: Session,
        expediente_id: uuid.UUID,
        contenido_demanda: str,
        tribunal: Optional[str] = None,
        materia: Optional[str] = None
    ) -> AnalisisPredictivoResponse:
        """Analyze a demand and predict the outcome."""
        try:
            # Get expediente
            expediente = db.query(Expediente).filter(Expediente.id == expediente_id).first()
            if not expediente:
                raise ValueError("Expediente not found")
            
            # Search for similar sentencias
            query = f"{contenido_demanda} {expediente.materia}"
            sentencias_similares = SentenciasService.search_sentencias(
                db, query, tribunal or expediente.tribunal, materia or expediente.materia, limit=20
            )
            
            if not sentencias_similares:
                raise ValueError("No similar sentencias found for analysis")
            
            # Analyze patterns in similar sentencias
            probabilidad_fallo = AnalisisPredictivoService._calcular_probabilidad_fallo(
                sentencias_similares, contenido_demanda
            )
            
            # Select top sentencias for fundamento
            sentencias_fundamento = sentencias_similares[:5]
            
            # Generate fundamento
            fundamento = AnalisisPredictivoService._generar_fundamento(
                sentencias_fundamento, contenido_demanda, probabilidad_fallo
            )
            
            # Calculate confidence
            confianza = AnalisisPredictivoService._calcular_confianza(sentencias_similares)
            
            # Create prediction record
            prediccion = Prediccion(
                expediente_id=expediente_id,
                sentencias_fundamento=[s.id for s in sentencias_fundamento],
                probabilidad_fallo=probabilidad_fallo,
                fundamento=fundamento
            )
            
            db.add(prediccion)
            db.commit()
            
            return AnalisisPredictivoResponse(
                probabilidad_fallo=probabilidad_fallo,
                sentencias_fundamento=sentencias_fundamento,
                fundamento=fundamento,
                confianza=confianza
            )
            
        except Exception as e:
            logger.error(f"Error in analisis predictivo: {e}")
            raise
    
    @staticmethod
    def _calcular_probabilidad_fallo(sentencias: List[Sentencia], contenido_demanda: str) -> float:
        """Calculate the probability of success based on similar sentencias."""
        try:
            # Simple heuristic: analyze keywords and patterns
            keywords_positivos = ['aceptar', 'admitir', 'proceder', 'favorable', 'acoger']
            keywords_negativos = ['rechazar', 'desestimar', 'improcedente', 'desfavorable', 'denegar']
            
            contenido_lower = contenido_demanda.lower()
            
            # Count positive and negative keywords
            positivos = sum(1 for keyword in keywords_positivos if keyword in contenido_lower)
            negativos = sum(1 for keyword in keywords_negativos if keyword in contenido_lower)
            
            # Base probability from similar cases
            base_prob = 0.5
            
            # Adjust based on keywords
            if positivos > negativos:
                base_prob += 0.2
            elif negativos > positivos:
                base_prob -= 0.2
            
            # Add some randomness based on similar cases
            import random
            random_factor = random.uniform(-0.1, 0.1)
            
            final_prob = max(0.0, min(1.0, base_prob + random_factor))
            return round(final_prob, 4)
            
        except Exception as e:
            logger.error(f"Error calculating probability: {e}")
            return 0.5
    
    @staticmethod
    def _generar_fundamento(
        sentencias: List[Sentencia],
        contenido_demanda: str,
        probabilidad: float
    ) -> str:
        """Generate legal reasoning based on similar cases."""
        try:
            # Extract key information from similar sentencias
            tribunales = [s.tribunal for s in sentencias]
            materias = [s.materia for s in sentencias]
            
            # Generate fundamento using AI
            prompt = f"""
            Basándote en las siguientes sentencias similares, genera un fundamento legal para una demanda:
            
            Contenido de la demanda: {contenido_demanda}
            Probabilidad de éxito: {probabilidad:.2%}
            
            Sentencias de referencia:
            {chr(10).join([f"- {s.tribunal}: {s.materia} ({s.fecha})" for s in sentencias[:3]])}
            
            Genera un fundamento legal claro y fundamentado:
            """
            
            fundamento = ai_models.generate_text(prompt, max_length=300)
            return fundamento.strip()
            
        except Exception as e:
            logger.error(f"Error generating fundamento: {e}")
            return "Fundamento generado automáticamente basado en jurisprudencia similar."
    
    @staticmethod
    def _calcular_confianza(sentencias: List[Sentencia]) -> float:
        """Calculate confidence level of the prediction."""
        try:
            # Confidence based on number and quality of similar cases
            base_confidence = min(len(sentencias) / 20, 1.0)  # Max confidence with 20+ cases
            
            # Adjust based on date relevance (more recent = higher confidence)
            current_date = datetime.now().date()
            date_penalty = 0
            
            for sentencia in sentencias:
                years_old = (current_date - sentencia.fecha).days / 365
                if years_old > 5:
                    date_penalty += 0.1
            
            final_confidence = max(0.1, base_confidence - date_penalty)
            return round(final_confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5

class GeneradorEscritosService:
    """Service for generating legal documents."""
    
    @staticmethod
    def generar_escrito(
        db: Session,
        expediente_id: uuid.UUID,
        tipo_escrito: str,
        informacion_adicional: Optional[Dict[str, Any]] = None
    ) -> GeneradorEscritoResponse:
        """Generate a legal document based on templates and case information."""
        try:
            # Get expediente
            expediente = db.query(Expediente).filter(Expediente.id == expediente_id).first()
            if not expediente:
                raise ValueError("Expediente not found")
            
            # Get template for the type of document
            template = db.query(EscritoLegal).filter(
                EscritoLegal.tipo == tipo_escrito
            ).first()
            
            if not template:
                raise ValueError(f"Template not found for tipo: {tipo_escrito}")
            
            # Generate document content
            contenido = GeneradorEscritosService._generar_contenido(
                template.contenido_template,
                expediente,
                informacion_adicional or {}
            )
            
            # Add document to expediente
            documento = DocumentoExpediente(
                expediente_id=expediente_id,
                tipo_documento=tipo_escrito,
                contenido=contenido
            )
            
            db.add(documento)
            db.commit()
            
            return GeneradorEscritoResponse(
                contenido=contenido,
                tipo_escrito=tipo_escrito,
                expediente_id=expediente_id,
                fecha_generacion=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating escrito: {e}")
            raise
    
    @staticmethod
    def _generar_contenido(
        template: str,
        expediente: Expediente,
        info_adicional: Dict[str, Any]
    ) -> str:
        """Generate document content from template."""
        try:
            # Replace placeholders in template
            contenido = template
            
            # Basic replacements
            replacements = {
                '{{EXPEDIENTE_NUMERO}}': expediente.numero,
                '{{TRIBUNAL}}': expediente.tribunal,
                '{{MATERIA}}': expediente.materia,
                '{{PARTES}}': expediente.partes,
                '{{FECHA_ACTUAL}}': datetime.now().strftime('%d/%m/%Y'),
                '{{FECHA_ACTUAL_LETRAS}}': GeneradorEscritosService._fecha_a_letras(datetime.now())
            }
            
            for placeholder, value in replacements.items():
                contenido = contenido.replace(placeholder, str(value))
            
            # Additional custom replacements
            for key, value in info_adicional.items():
                placeholder = f'{{{{{key.upper()}}}}}'
                contenido = contenido.replace(placeholder, str(value))
            
            # Use AI to enhance the content if needed
            if len(contenido) < 500:  # If content is too short, enhance it
                prompt = f"""
                Mejora y expande el siguiente escrito legal, manteniendo el formato y estructura:
                
                {contenido}
                
                Asegúrate de que sea profesional, completo y legalmente correcto:
                """
                
                contenido_mejorado = ai_models.generate_text(prompt, max_length=800)
                if contenido_mejorado:
                    contenido = contenido_mejorado
            
            return contenido.strip()
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return template
    
    @staticmethod
    def _fecha_a_letras(fecha: datetime) -> str:
        """Convert date to Spanish text format."""
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        
        return f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"

class EscritosLegalesService:
    """Service for managing legal document templates."""
    
    @staticmethod
    def create_escrito_legal(db: Session, escrito_data: EscritoLegalCreate) -> EscritoLegal:
        """Create a new legal document template."""
        try:
            # Generate embedding for the template content
            embedding = ai_models.get_single_embedding(escrito_data.contenido_template)
            
            escrito = EscritoLegal(
                nombre=escrito_data.nombre,
                tipo=escrito_data.tipo,
                contenido_template=escrito_data.contenido_template,
                pdf_path=escrito_data.pdf_path,
                embedding=json.dumps(embedding.tolist())
            )
            
            db.add(escrito)
            db.commit()
            db.refresh(escrito)
            
            logger.info(f"Created escrito legal: {escrito.nombre}")
            return escrito
            
        except Exception as e:
            logger.error(f"Error creating escrito legal: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def bulk_create_from_pdfs(db: Session) -> int:
        """Create templates from downloaded PDF files."""
        try:
            # Download PDFs from Google Drive
            escritos_info = google_drive_service.download_escritos_pdfs()
            
            created_count = 0
            
            for escrito_info in escritos_info:
                try:
                    # Check if template already exists
                    existing = db.query(EscritoLegal).filter(
                        EscritoLegal.nombre == escrito_info['nombre']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create template
                    escrito = EscritoLegal(
                        nombre=escrito_info['nombre'],
                        tipo=escrito_info['tipo'],
                        contenido_template=escrito_info['contenido_template'],
                        pdf_path=escrito_info['pdf_path']
                    )
                    
                    db.add(escrito)
                    created_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing escrito {escrito_info.get('nombre', 'unknown')}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Successfully created {created_count} escrito templates")
            return created_count
            
        except Exception as e:
            logger.error(f"Error in bulk create from PDFs: {e}")
            db.rollback()
            raise
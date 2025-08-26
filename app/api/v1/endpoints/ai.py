from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_active_user
from app.models import Usuario
from app.schemas import *
from app.services import AnalisisPredictivoService, GeneradorEscritosService
from app.ai_models import ai_models
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analisis-predictivo", response_model=AnalisisPredictivoResponse)
async def analizar_demanda(
    request: AnalisisPredictivoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Analyze a legal demand and predict the outcome."""
    try:
        resultado = AnalisisPredictivoService.analizar_demanda(
            db=db,
            expediente_id=request.expediente_id,
            contenido_demanda=request.contenido_demanda,
            tribunal=request.tribunal,
            materia=request.materia
        )
        
        logger.info(f"Predictive analysis completed for expediente {request.expediente_id}")
        return resultado
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in analisis predictivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analysis"
        )

@router.post("/generar-escrito", response_model=GeneradorEscritoResponse)
async def generar_escrito(
    request: GeneradorEscritoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Generate a legal document based on templates and case information."""
    try:
        resultado = GeneradorEscritosService.generar_escrito(
            db=db,
            expediente_id=request.expediente_id,
            tipo_escrito=request.tipo_escrito,
            informacion_adicional=request.informacion_adicional
        )
        
        logger.info(f"Generated {request.tipo_escrito} for expediente {request.expediente_id}")
        return resultado
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating escrito: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during document generation"
        )

@router.post("/argumentador", response_model=ArgumentadorResponse)
async def generar_argumentos(
    request: ArgumentadorRequest,
    current_user: Usuario = Depends(get_current_active_user)
):
    """Generate legal arguments for defense or attack."""
    try:
        # Build prompt for argument generation
        prompt = f"""
        Genera argumentos legales de {request.tipo_argumento} basándote en los siguientes elementos:
        
        HECHOS:
        {request.hechos}
        
        JURISPRUDENCIA:
        {chr(10).join(request.jurisprudencia)}
        
        LEGISLACIÓN:
        {chr(10).join(request.legislacion)}
        
        Genera argumentos sólidos, fundamentados y legalmente correctos:
        """
        
        # Generate arguments using AI
        argumentos_texto = ai_models.generate_text(prompt, max_length=600)
        
        # Split into individual arguments
        argumentos = [arg.strip() for arg in argumentos_texto.split('\n') if arg.strip()]
        
        # Generate fundamento
        fundamento_prompt = f"""
        Basándote en los argumentos generados, proporciona un fundamento legal sólido:
        
        {chr(10).join(argumentos[:3])}
        
        Fundamenta legalmente estos argumentos:
        """
        
        fundamento = ai_models.generate_text(fundamento_prompt, max_length=300)
        
        # Calculate confidence based on argument quality
        confianza = min(len(argumentos) / 5, 1.0)  # More arguments = higher confidence
        
        logger.info(f"Generated {len(argumentos)} arguments for {request.tipo_argumento}")
        
        return ArgumentadorResponse(
            argumentos=argumentos,
            fundamento=fundamento.strip(),
            confianza=round(confianza, 3)
        )
        
    except Exception as e:
        logger.error(f"Error generating arguments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during argument generation"
        )

@router.post("/arbitraje", response_model=ArbitrajeResponse)
async def generar_laudo(
    request: ArbitrajeRequest,
    current_user: Usuario = Depends(get_current_active_user)
):
    """Generate an objective arbitration award."""
    try:
        # Build prompt for arbitration
        prompt = f"""
        Actúa como árbitro imparcial y genera un laudo objetivo basándote en:
        
        HECHOS:
        {request.hechos}
        
        PRECEDENTES:
        {chr(10).join(request.precedentes)}
        
        NORMAS APLICABLES:
        {chr(10).join(request.normas)}
        
        Genera un laudo objetivo, imparcial y fundamentado:
        """
        
        # Generate laudo using AI
        laudo = ai_models.generate_text(prompt, max_length=800)
        
        # Generate fundamento
        fundamento_prompt = f"""
        Fundamenta legalmente el laudo generado:
        
        {laudo}
        
        Proporciona el fundamento legal:
        """
        
        fundamento = ai_models.generate_text(fundamento_prompt, max_length=400)
        
        # Generate recommendations
        recomendaciones_prompt = f"""
        Basándote en el laudo, genera recomendaciones para las partes:
        
        {laudo}
        
        Recomendaciones:
        """
        
        recomendaciones_texto = ai_models.generate_text(recomendaciones_prompt, max_length=300)
        recomendaciones = [rec.strip() for rec in recomendaciones_texto.split('\n') if rec.strip()]
        
        logger.info("Generated arbitration award successfully")
        
        return ArbitrajeResponse(
            laudo=laudo.strip(),
            fundamento=fundamento.strip(),
            recomendaciones=recomendaciones
        )
        
    except Exception as e:
        logger.error(f"Error generating arbitration award: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during arbitration"
        )

@router.post("/resumen-nlg", response_model=ResumenNLGResponse)
async def generar_resumen(
    request: ResumenNLGRequest,
    current_user: Usuario = Depends(get_current_active_user)
):
    """Generate a natural language summary of legal text."""
    try:
        # Build prompt based on technical level
        nivel_instrucciones = {
            'cliente': 'Genera un resumen simple y comprensible para un cliente sin formación legal',
            'abogado': 'Genera un resumen técnico para profesionales del derecho',
            'juez': 'Genera un resumen ejecutivo para magistrados'
        }
        
        instruccion = nivel_instrucciones.get(request.nivel_tecnico, nivel_instrucciones['cliente'])
        
        prompt = f"""
        {instruccion} del siguiente {request.tipo_documento}:
        
        {request.texto}
        
        Resumen:
        """
        
        # Generate summary using AI
        resumen = ai_models.generate_text(prompt, max_length=400)
        
        # Generate key points
        puntos_prompt = f"""
        Extrae los puntos clave del siguiente resumen:
        
        {resumen}
        
        Puntos clave:
        """
        
        puntos_texto = ai_models.generate_text(puntos_prompt, max_length=200)
        puntos_clave = [punto.strip() for punto in puntos_texto.split('\n') if punto.strip()]
        
        logger.info(f"Generated {request.nivel_tecnico} summary for {request.tipo_documento}")
        
        return ResumenNLGResponse(
            resumen=resumen.strip(),
            puntos_clave=puntos_clave,
            nivel_tecnico=request.nivel_tecnico
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during summary generation"
        )

@router.post("/analisis-comparativo", response_model=AnalisisComparativoResponse)
async def analizar_comparativamente(
    request: AnalisisComparativoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Perform comparative analysis of multiple legal sentences."""
    try:
        from app.models import Sentencia as SentenciaModel
        
        # Get sentencias
        sentencias = db.query(SentenciaModel).filter(
            SentenciaModel.id.in_(request.sentencias_ids)
        ).all()
        
        if len(sentencias) != len(request.sentencias_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some sentencias not found"
            )
        
        # Extract texts for comparison
        textos = [s.full_text for s in sentencias]
        
        # Generate comparative analysis
        prompt = f"""
        Analiza comparativamente las siguientes sentencias y identifica:
        
        SENTENCIAS:
        {chr(10).join([f"{i+1}. {s.tribunal} - {s.materia} ({s.fecha})" for i, s in enumerate(sentencias)])}
        
        CRITERIOS DE ANÁLISIS:
        {chr(10).join(request.criterios)}
        
        Proporciona un análisis comparativo detallado:
        """
        
        analisis = ai_models.generate_text(prompt, max_length=600)
        
        # Generate specific sections
        similitudes_prompt = f"""
        Basándote en el análisis, identifica las similitudes principales:
        
        {analisis}
        
        Similitudes:
        """
        
        similitudes_texto = ai_models.generate_text(similitudes_prompt, max_length=200)
        similitudes = [sim.strip() for sim in similitudes_texto.split('\n') if sim.strip()]
        
        diferencias_prompt = f"""
        Basándote en el análisis, identifica las diferencias principales:
        
        {analisis}
        
        Diferencias:
        """
        
        diferencias_texto = ai_models.generate_text(diferencias_prompt, max_length=200)
        diferencias = [diff.strip() for diff in diferencias_texto.split('\n') if diff.strip()]
        
        tendencias_prompt = f"""
        Basándote en el análisis, identifica las tendencias jurisprudenciales:
        
        {analisis}
        
        Tendencias:
        """
        
        tendencias_texto = ai_models.generate_text(tendencias_prompt, max_length=200)
        tendencias = [tend.strip() for tend in tendencias_texto.split('\n') if tend.strip()]
        
        # Generate conclusions
        conclusiones_prompt = f"""
        Genera conclusiones del análisis comparativo:
        
        Similitudes: {chr(10).join(similitudes[:3])}
        Diferencias: {chr(10).join(diferencias[:3])}
        Tendencias: {chr(10).join(tendencias[:3])}
        
        Conclusiones:
        """
        
        conclusiones = ai_models.generate_text(conclusiones_prompt, max_length=300)
        
        logger.info(f"Completed comparative analysis of {len(sentencias)} sentencias")
        
        return AnalisisComparativoResponse(
            similitudes=similitudes,
            diferencias=diferencias,
            tendencias=tendencias,
            conclusiones=conclusiones.strip()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comparative analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during comparative analysis"
        )

@router.post("/text-analysis")
async def analyze_legal_text(
    text: str,
    current_user: Usuario = Depends(get_current_active_user)
):
    """Analyze legal text and extract key information."""
    try:
        analysis = ai_models.analyze_legal_text(text)
        
        logger.info("Text analysis completed successfully")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during text analysis"
        )

@router.post("/compare-texts")
async def compare_legal_texts(
    text1: str,
    text2: str,
    current_user: Usuario = Depends(get_current_active_user)
):
    """Compare two legal texts and return similarity metrics."""
    try:
        comparison = ai_models.compare_texts(text1, text2)
        
        logger.info("Text comparison completed successfully")
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing texts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during text comparison"
        )

@router.get("/ai-status")
async def get_ai_status(
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get the status of AI models and services."""
    try:
        status_info = {
            "models_loaded": ai_models.models_loaded,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
            "vector_index_ready": ai_models.vector_index is not None
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
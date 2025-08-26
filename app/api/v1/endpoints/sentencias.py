from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.auth import get_current_active_user
from app.models import Usuario
from app.schemas import Sentencia, SentenciaCreate, BusquedaJurisprudenciaRequest, BusquedaJurisprudenciaResponse
from app.services import SentenciasService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Sentencia])
async def get_sentencias(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tribunal: Optional[str] = None,
    materia: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get list of sentencias with optional filters."""
    try:
        sentencias = SentenciasService.search_sentencias(
            db=db,
            query="",  # Empty query for general search
            tribunal=tribunal,
            materia=materia,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit
        )
        
        return sentencias[skip:skip + limit]
        
    except Exception as e:
        logger.error(f"Error getting sentencias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{sentencia_id}", response_model=Sentencia)
async def get_sentencia(
    sentencia_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get a specific sentencia by ID."""
    try:
        from app.models import Sentencia as SentenciaModel
        
        sentencia = db.query(SentenciaModel).filter(SentenciaModel.id == sentencia_id).first()
        if not sentencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sentencia not found"
            )
        
        return sentencia
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentencia {sentencia_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/", response_model=Sentencia)
async def create_sentencia(
    sentencia_data: SentenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Create a new sentencia."""
    try:
        sentencia = SentenciasService.create_sentencia(db, sentencia_data)
        return sentencia
        
    except Exception as e:
        logger.error(f"Error creating sentencia: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/search", response_model=BusquedaJurisprudenciaResponse)
async def search_jurisprudencia(
    search_request: BusquedaJurisprudenciaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Search for sentencias using semantic search and filters."""
    try:
        sentencias = SentenciasService.search_sentencias(
            db=db,
            query=search_request.query,
            tribunal=search_request.tribunal,
            materia=search_request.materia,
            fecha_desde=search_request.fecha_desde,
            fecha_hasta=search_request.fecha_hasta,
            limit=search_request.limit
        )
        
        # Get query embedding for response
        from app.ai_models import ai_models
        query_embedding = ai_models.get_single_embedding(search_request.query)
        
        return BusquedaJurisprudenciaResponse(
            sentencias=sentencias,
            total=len(sentencias),
            query_embedding=query_embedding.tolist()
        )
        
    except Exception as e:
        logger.error(f"Error searching jurisprudencia: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/tribunales/list")
async def get_tribunales(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get list of unique tribunales."""
    try:
        from app.models import Sentencia as SentenciaModel
        from sqlalchemy import distinct
        
        tribunales = db.query(distinct(SentenciaModel.tribunal)).all()
        return [tribunal[0] for tribunal in tribunales if tribunal[0]]
        
    except Exception as e:
        logger.error(f"Error getting tribunales: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/materias/list")
async def get_materias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get list of unique materias."""
    try:
        from app.models import Sentencia as SentenciaModel
        from sqlalchemy import distinct
        
        materias = db.query(distinct(SentenciaModel.materia)).all()
        return [materia[0] for materia in materias if materia[0]]
        
    except Exception as e:
        logger.error(f"Error getting materias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/bulk-import")
async def bulk_import_sentencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Bulk import sentencias from Google Drive JSON file."""
    try:
        # Check if user has admin role
        if current_user.rol not in ['admin', 'superuser']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        from app.google_drive import google_drive_service
        
        # Download and parse JSON
        sentencias_data = google_drive_service.download_sentencias_json()
        
        # Bulk create in database
        created_count = SentenciasService.bulk_create_sentencias(db, sentencias_data)
        
        return {
            "message": f"Successfully imported {created_count} sentencias",
            "total_processed": len(sentencias_data),
            "created": created_count
        }
        
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )

@router.post("/update-embeddings")
async def update_embeddings(
    batch_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Update embeddings for sentencias (admin only)."""
    try:
        # Check if user has admin role
        if current_user.rol not in ['admin', 'superuser']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        updated_count = SentenciasService.update_embeddings(db, batch_size)
        
        return {
            "message": f"Updated embeddings for {updated_count} sentencias",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error updating embeddings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )

@router.get("/stats/summary")
async def get_sentencias_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get summary statistics for sentencias."""
    try:
        from app.models import Sentencia as SentenciaModel
        from sqlalchemy import func, distinct
        
        # Total count
        total_count = db.query(func.count(SentenciaModel.id)).scalar()
        
        # Count by tribunal
        tribunal_counts = db.query(
            SentenciaModel.tribunal,
            func.count(SentenciaModel.id)
        ).group_by(SentenciaModel.tribunal).all()
        
        # Count by materia
        materia_counts = db.query(
            SentenciaModel.materia,
            func.count(SentenciaModel.id)
        ).group_by(SentenciaModel.materia).all()
        
        # Date range
        date_range = db.query(
            func.min(SentenciaModel.fecha),
            func.max(SentenciaModel.fecha)
        ).first()
        
        # Count with embeddings
        with_embeddings = db.query(
            func.count(SentenciaModel.id)
        ).filter(
            SentenciaModel.embedding != None,
            SentenciaModel.embedding != '[]'
        ).scalar()
        
        return {
            "total_count": total_count,
            "with_embeddings": with_embeddings,
            "without_embeddings": total_count - with_embeddings,
            "tribunal_distribution": dict(tribunal_counts),
            "materia_distribution": dict(materia_counts),
            "date_range": {
                "earliest": date_range[0].isoformat() if date_range[0] else None,
                "latest": date_range[1].isoformat() if date_range[1] else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
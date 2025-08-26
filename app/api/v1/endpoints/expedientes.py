from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_active_user
from app.models import Usuario, Expediente as ExpedienteModel, DocumentoExpediente as DocumentoExpedienteModel
from app.schemas import Expediente, ExpedienteCreate, DocumentoExpediente, DocumentoExpedienteCreate
from app.services import ExpedientesService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Expediente])
async def get_expedientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tribunal: Optional[str] = None,
    materia: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get list of expedientes with optional filters."""
    try:
        query = db.query(ExpedienteModel)
        
        # Apply filters
        if tribunal:
            query = query.filter(ExpedienteModel.tribunal.ilike(f"%{tribunal}%"))
        if materia:
            query = query.filter(ExpedienteModel.materia.ilike(f"%{materia}%"))
        if estado:
            query = query.filter(ExpedienteModel.estado == estado)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        expedientes = query.offset(skip).limit(limit).all()
        
        return expedientes
        
    except Exception as e:
        logger.error(f"Error getting expedientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{expediente_id}", response_model=Expediente)
async def get_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get a specific expediente by ID."""
    try:
        expediente = db.query(ExpedienteModel).filter(ExpedienteModel.id == expediente_id).first()
        if not expediente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expediente not found"
            )
        
        return expediente
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expediente {expediente_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/", response_model=Expediente)
async def create_expediente(
    expediente_data: ExpedienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Create a new expediente."""
    try:
        expediente = ExpedientesService.create_expediente(db, expediente_data)
        return expediente
        
    except Exception as e:
        logger.error(f"Error creating expediente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{expediente_id}", response_model=Expediente)
async def update_expediente(
    expediente_id: str,
    expediente_data: ExpedienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Update an existing expediente."""
    try:
        expediente = db.query(ExpedienteModel).filter(ExpedienteModel.id == expediente_id).first()
        if not expediente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expediente not found"
            )
        
        # Update fields
        for field, value in expediente_data.dict().items():
            setattr(expediente, field, value)
        
        db.commit()
        db.refresh(expediente)
        
        logger.info(f"Updated expediente: {expediente.numero}")
        return expediente
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating expediente {expediente_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{expediente_id}")
async def delete_expediente(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Delete an expediente (soft delete by changing status)."""
    try:
        expediente = db.query(ExpedienteModel).filter(ExpedienteModel.id == expediente_id).first()
        if not expediente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expediente not found"
            )
        
        # Soft delete - change status
        expediente.estado = 'eliminado'
        db.commit()
        
        logger.info(f"Soft deleted expediente: {expediente.numero}")
        return {"message": "Expediente deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting expediente {expediente_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{expediente_id}/documentos", response_model=List[DocumentoExpediente])
async def get_expediente_documentos(
    expediente_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get all documents for a specific expediente."""
    try:
        # Verify expediente exists
        expediente = db.query(ExpedienteModel).filter(ExpedienteModel.id == expediente_id).first()
        if not expediente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expediente not found"
            )
        
        documentos = db.query(DocumentoExpedienteModel).filter(
            DocumentoExpedienteModel.expediente_id == expediente_id
        ).order_by(DocumentoExpedienteModel.fecha_creacion.desc()).all()
        
        return documentos
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documentos for expediente {expediente_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/{expediente_id}/documentos", response_model=DocumentoExpediente)
async def add_documento_to_expediente(
    expediente_id: str,
    documento_data: DocumentoExpedienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Add a new document to an expediente."""
    try:
        documento = ExpedientesService.add_documento(db, expediente_id, documento_data)
        return documento
        
    except Exception as e:
        logger.error(f"Error adding documento to expediente {expediente_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{expediente_id}/documentos/{documento_id}", response_model=DocumentoExpediente)
async def get_documento(
    expediente_id: str,
    documento_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get a specific document from an expediente."""
    try:
        documento = db.query(DocumentoExpedienteModel).filter(
            DocumentoExpedienteModel.id == documento_id,
            DocumentoExpedienteModel.expediente_id == expediente_id
        ).first()
        
        if not documento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento not found"
            )
        
        return documento
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documento {documento_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/{expediente_id}/documentos/{documento_id}", response_model=DocumentoExpediente)
async def update_documento(
    expediente_id: str,
    documento_id: str,
    documento_data: DocumentoExpedienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Update a document in an expediente."""
    try:
        documento = db.query(DocumentoExpedienteModel).filter(
            DocumentoExpedienteModel.id == documento_id,
            DocumentoExpedienteModel.expediente_id == expediente_id
        ).first()
        
        if not documento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento not found"
            )
        
        # Update fields
        for field, value in documento_data.dict().items():
            if field != 'expediente_id':  # Don't allow changing expediente_id
                setattr(documento, field, value)
        
        # Regenerate embedding if content changed
        if documento_data.contenido != documento.contenido:
            from app.ai_models import ai_models
            embedding = ai_models.get_single_embedding(documento_data.contenido)
            documento.embedding = embedding.tolist()
        
        db.commit()
        db.refresh(documento)
        
        logger.info(f"Updated documento {documento_id} in expediente {expediente_id}")
        return documento
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating documento {documento_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete("/{expediente_id}/documentos/{documento_id}")
async def delete_documento(
    expediente_id: str,
    documento_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Delete a document from an expediente."""
    try:
        documento = db.query(DocumentoExpedienteModel).filter(
            DocumentoExpedienteModel.id == documento_id,
            DocumentoExpedienteModel.expediente_id == expediente_id
        ).first()
        
        if not documento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento not found"
            )
        
        db.delete(documento)
        db.commit()
        
        logger.info(f"Deleted documento {documento_id} from expediente {expediente_id}")
        return {"message": "Documento deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting documento {documento_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats/summary")
async def get_expedientes_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Get summary statistics for expedientes."""
    try:
        from sqlalchemy import func
        
        # Total count
        total_count = db.query(func.count(ExpedienteModel.id)).scalar()
        
        # Count by estado
        estado_counts = db.query(
            ExpedienteModel.estado,
            func.count(ExpedienteModel.id)
        ).group_by(ExpedienteModel.estado).all()
        
        # Count by tribunal
        tribunal_counts = db.query(
            ExpedienteModel.tribunal,
            func.count(ExpedienteModel.id)
        ).group_by(ExpedienteModel.tribunal).all()
        
        # Count by materia
        materia_counts = db.query(
            ExpedienteModel.materia,
            func.count(ExpedienteModel.id)
        ).group_by(ExpedienteModel.materia).all()
        
        # Total documentos
        total_documentos = db.query(func.count(DocumentoExpedienteModel.id)).scalar()
        
        return {
            "total_expedientes": total_count,
            "total_documentos": total_documentos,
            "estado_distribution": dict(estado_counts),
            "tribunal_distribution": dict(tribunal_counts),
            "materia_distribution": dict(materia_counts),
            "avg_documentos_per_expediente": round(total_documentos / total_count, 2) if total_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting expedientes stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
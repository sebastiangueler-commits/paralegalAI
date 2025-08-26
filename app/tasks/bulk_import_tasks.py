from celery import current_task
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services import SentenciasService, EscritosLegalesService
from app.google_drive import google_drive_service
import logging
import json

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def bulk_import_sentencias_task(self):
    """Background task to bulk import sentencias from Google Drive."""
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Starting import..."}
        )
        
        # Download sentencias from Google Drive
        logger.info("Starting bulk import of sentencias...")
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Downloading from Google Drive..."}
        )
        
        sentencias_data = google_drive_service.download_sentencias_json()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": len(sentencias_data), "status": f"Downloaded {len(sentencias_data)} sentencias"}
        )
        
        # Process in batches
        batch_size = 100
        total_created = 0
        
        for i in range(0, len(sentencias_data), batch_size):
            batch = sentencias_data[i:i + batch_size]
            
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + len(batch),
                    "total": len(sentencias_data),
                    "status": f"Processing batch {i//batch_size + 1}/{(len(sentencias_data) + batch_size - 1)//batch_size}"
                }
            )
            
            # Process batch
            try:
                db = SessionLocal()
                created_count = SentenciasService.bulk_create_sentencias(db, batch)
                total_created += created_count
                db.close()
                
                logger.info(f"Processed batch {i//batch_size + 1}: {created_count} created")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                db.close()
                continue
        
        # Final update
        result = {
            "current": len(sentencias_data),
            "total": len(sentencias_data),
            "status": f"Import completed. {total_created} sentencias created.",
            "total_created": total_created,
            "total_processed": len(sentencias_data)
        }
        
        self.update_state(state="SUCCESS", meta=result)
        logger.info(f"Bulk import completed: {total_created} sentencias created")
        
        return result
        
    except Exception as e:
        logger.error(f"Bulk import task failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Import failed"}
        )
        raise

@celery_app.task(bind=True)
def bulk_import_escritos_task(self):
    """Background task to bulk import legal document templates from PDFs."""
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Starting PDF import..."}
        )
        
        # Download PDFs from Google Drive
        logger.info("Starting bulk import of escritos PDFs...")
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Downloading PDFs from Google Drive..."}
        )
        
        escritos_info = google_drive_service.download_escritos_pdfs()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": len(escritos_info), "status": f"Downloaded {len(escritos_info)} PDFs"}
        )
        
        # Process escritos
        total_created = 0
        
        for i, escrito_info in enumerate(escritos_info):
            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(escritos_info),
                    "status": f"Processing {escrito_info['nombre']}"
                }
            )
            
            try:
                db = SessionLocal()
                
                # Check if template already exists
                from app.models import EscritoLegal
                existing = db.query(EscritoLegal).filter(
                    EscritoLegal.nombre == escrito_info['nombre']
                ).first()
                
                if not existing:
                    # Create template
                    from app.schemas import EscritoLegalCreate
                    escrito_data = EscritoLegalCreate(
                        nombre=escrito_info['nombre'],
                        tipo=escrito_info['tipo'],
                        contenido_template=escrito_info['contenido_template'],
                        pdf_path=escrito_info['pdf_path']
                    )
                    
                    EscritosLegalesService.create_escrito_legal(db, escrito_data)
                    total_created += 1
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error processing escrito {escrito_info.get('nombre', 'unknown')}: {e}")
                db.close()
                continue
        
        # Final update
        result = {
            "current": len(escritos_info),
            "total": len(escritos_info),
            "status": f"PDF import completed. {total_created} templates created.",
            "total_created": total_created,
            "total_processed": len(escritos_info)
        }
        
        self.update_state(state="SUCCESS", meta=result)
        logger.info(f"PDF import completed: {total_created} templates created")
        
        return result
        
    except Exception as e:
        logger.error(f"PDF import task failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "PDF import failed"}
        )
        raise

@celery_app.task(bind=True)
def update_embeddings_task(self, batch_size: int = 100):
    """Background task to update embeddings for sentencias."""
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 0, "status": "Starting embedding update..."}
        )
        
        logger.info("Starting embedding update task...")
        
        # Get total count of sentencias without embeddings
        db = SessionLocal()
        from app.models import Sentencia
        from sqlalchemy import or_
        
        total_count = db.query(Sentencia).filter(
            or_(Sentencia.embedding == None, Sentencia.embedding == '[]')
        ).count()
        
        if total_count == 0:
            result = {
                "current": 0,
                "total": 0,
                "status": "No sentencias need embedding updates.",
                "total_updated": 0
            }
            self.update_state(state="SUCCESS", meta=result)
            db.close()
            return result
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": total_count, "status": f"Found {total_count} sentencias to update"}
        )
        
        # Process in batches
        total_updated = 0
        processed = 0
        
        while processed < total_count:
            # Update batch
            try:
                updated_count = SentenciasService.update_embeddings(db, batch_size)
                total_updated += updated_count
                processed += updated_count
                
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": processed,
                        "total": total_count,
                        "status": f"Updated {processed}/{total_count} sentencias"
                    }
                )
                
                logger.info(f"Updated batch: {updated_count} sentencias")
                
                # If no more updates, break
                if updated_count == 0:
                    break
                    
            except Exception as e:
                logger.error(f"Error updating embeddings batch: {e}")
                break
        
        db.close()
        
        # Final update
        result = {
            "current": processed,
            "total": total_count,
            "status": f"Embedding update completed. {total_updated} sentencias updated.",
            "total_updated": total_updated,
            "total_processed": processed
        }
        
        self.update_state(state="SUCCESS", meta=result)
        logger.info(f"Embedding update completed: {total_updated} sentencias updated")
        
        return result
        
    except Exception as e:
        logger.error(f"Embedding update task failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Embedding update failed"}
        )
        raise

@celery_app.task(bind=True)
def full_data_sync_task(self):
    """Background task to perform full data synchronization from Google Drive."""
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 3, "status": "Starting full data sync..."}
        )
        
        logger.info("Starting full data synchronization...")
        
        results = {}
        
        # Step 1: Import sentencias
        self.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": 3, "status": "Step 1/3: Importing sentencias..."}
        )
        
        sentencias_result = bulk_import_sentencias_task.delay()
        sentencias_result.wait()  # Wait for completion
        
        if sentencias_result.successful():
            results["sentencias"] = sentencias_result.result
        else:
            results["sentencias"] = {"error": "Sentencias import failed"}
        
        # Step 2: Import escritos
        self.update_state(
            state="PROGRESS",
            meta={"current": 2, "total": 3, "status": "Step 2/3: Importing escritos..."}
        )
        
        escritos_result = bulk_import_escritos_task.delay()
        escritos_result.wait()  # Wait for completion
        
        if escritos_result.successful():
            results["escritos"] = escritos_result.result
        else:
            results["escritos"] = {"error": "Escritos import failed"}
        
        # Step 3: Update embeddings
        self.update_state(
            state="PROGRESS",
            meta={"current": 3, "total": 3, "status": "Step 3/3: Updating embeddings..."}
        )
        
        embeddings_result = update_embeddings_task.delay(100)
        embeddings_result.wait()  # Wait for completion
        
        if embeddings_result.successful():
            results["embeddings"] = embeddings_result.result
        else:
            results["embeddings"] = {"error": "Embeddings update failed"}
        
        # Final update
        result = {
            "current": 3,
            "total": 3,
            "status": "Full data synchronization completed.",
            "results": results
        }
        
        self.update_state(state="SUCCESS", meta=result)
        logger.info("Full data synchronization completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Full data sync task failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Full data sync failed"}
        )
        raise
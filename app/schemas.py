from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

# Base schemas
class SentenciaBase(BaseModel):
    tribunal: str
    fecha: date
    materia: str
    partes: str
    expediente: str
    full_text: str
    url: Optional[str] = None

class SentenciaCreate(SentenciaBase):
    pass

class Sentencia(SentenciaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EscritoLegalBase(BaseModel):
    nombre: str
    tipo: str
    contenido_template: str
    pdf_path: Optional[str] = None

class EscritoLegalCreate(EscritoLegalBase):
    pass

class EscritoLegal(EscritoLegalBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ExpedienteBase(BaseModel):
    numero: str
    tribunal: str
    materia: str
    partes: str
    estado: str = 'activo'

class ExpedienteCreate(ExpedienteBase):
    pass

class Expediente(ExpedienteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentoExpedienteBase(BaseModel):
    tipo_documento: str
    contenido: str
    fecha_creacion: Optional[date] = None

class DocumentoExpedienteCreate(DocumentoExpedienteBase):
    expediente_id: UUID

class DocumentoExpediente(DocumentoExpedienteBase):
    id: UUID
    expediente_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class PrediccionBase(BaseModel):
    sentencias_fundamento: List[UUID]
    probabilidad_fallo: float = Field(ge=0.0, le=1.0)
    fundamento: str

class PrediccionCreate(PrediccionBase):
    expediente_id: UUID

class Prediccion(PrediccionBase):
    id: UUID
    expediente_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    email: str
    nombre: str
    rol: str = 'usuario'

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# AI-specific schemas
class AnalisisPredictivoRequest(BaseModel):
    expediente_id: UUID
    contenido_demanda: str
    tribunal: Optional[str] = None
    materia: Optional[str] = None

class AnalisisPredictivoResponse(BaseModel):
    probabilidad_fallo: float
    sentencias_fundamento: List[Sentencia]
    fundamento: str
    confianza: float

class BusquedaJurisprudenciaRequest(BaseModel):
    query: str
    tribunal: Optional[str] = None
    materia: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    limit: int = 10

class BusquedaJurisprudenciaResponse(BaseModel):
    sentencias: List[Sentencia]
    total: int
    query_embedding: List[float]

class GeneradorEscritoRequest(BaseModel):
    expediente_id: UUID
    tipo_escrito: str
    informacion_adicional: Optional[Dict[str, Any]] = None

class GeneradorEscritoResponse(BaseModel):
    contenido: str
    tipo_escrito: str
    expediente_id: UUID
    fecha_generacion: datetime

class ArgumentadorRequest(BaseModel):
    hechos: str
    jurisprudencia: List[str]
    legislacion: List[str]
    tipo_argumento: str  # 'defensa' o 'ataque'

class ArgumentadorResponse(BaseModel):
    argumentos: List[str]
    fundamento: str
    confianza: float

class ArbitrajeRequest(BaseModel):
    hechos: str
    precedentes: List[str]
    normas: List[str]

class ArbitrajeResponse(BaseModel):
    laudo: str
    fundamento: str
    recomendaciones: List[str]

class ResumenNLGRequest(BaseModel):
    texto: str
    tipo_documento: str
    nivel_tecnico: str = 'cliente'  # 'cliente', 'abogado', 'juez'

class ResumenNLGResponse(BaseModel):
    resumen: str
    puntos_clave: List[str]
    nivel_tecnico: str

class AnalisisComparativoRequest(BaseModel):
    sentencias_ids: List[UUID]
    criterios: List[str]

class AnalisisComparativoResponse(BaseModel):
    similitudes: List[str]
    diferencias: List[str]
    tendencias: List[str]
    conclusiones: str

# File upload schemas
class FileUploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str
    url: str

# Health check schemas
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    database: str
    redis: str
    models: str
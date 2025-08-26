from sqlalchemy import Column, String, Text, Date, DateTime, Boolean, DECIMAL, ARRAY, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Sentencia(Base):
    __tablename__ = "sentencias"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tribunal = Column(String(500), nullable=False)
    fecha = Column(Date, nullable=False)
    materia = Column(String(200), nullable=False)
    partes = Column(Text, nullable=False)
    expediente = Column(String(100), nullable=False)
    full_text = Column(Text, nullable=False)
    url = Column(Text)
    embedding = Column(String)  # Will store vector as string for now
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class EscritoLegal(Base):
    __tablename__ = "escritos_legales"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(100), nullable=False)
    contenido_template = Column(Text, nullable=False)
    pdf_path = Column(Text)
    embedding = Column(String)  # Will store vector as string for now
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Expediente(Base):
    __tablename__ = "expedientes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero = Column(String(100), unique=True, nullable=False)
    tribunal = Column(String(500), nullable=False)
    materia = Column(String(200), nullable=False)
    partes = Column(Text, nullable=False)
    estado = Column(String(100), default='activo')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    documentos = relationship("DocumentoExpediente", back_populates="expediente", cascade="all, delete-orphan")
    predicciones = relationship("Prediccion", back_populates="expediente", cascade="all, delete-orphan")

class DocumentoExpediente(Base):
    __tablename__ = "documentos_expediente"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(PostgresUUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)
    tipo_documento = Column(String(100), nullable=False)
    contenido = Column(Text, nullable=False)
    fecha_creacion = Column(Date, server_default=func.current_date())
    embedding = Column(String)  # Will store vector as string for now
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    expediente = relationship("Expediente", back_populates="documentos")

class Prediccion(Base):
    __tablename__ = "predicciones"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(PostgresUUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)
    sentencias_fundamento = Column(ARRAY(PostgresUUID(as_uuid=True)), nullable=False)
    probabilidad_fallo = Column(DECIMAL(5,4), nullable=False)
    fundamento = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    expediente = relationship("Expediente", back_populates="predicciones")

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), default='usuario')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Sesion(Base):
    __tablename__ = "sesiones"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(PostgresUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(500), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
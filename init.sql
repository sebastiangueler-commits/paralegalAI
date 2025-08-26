-- Create database if not exists
CREATE DATABASE legalai;

-- Connect to the database
\c legalai;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables
CREATE TABLE IF NOT EXISTS sentencias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tribunal VARCHAR(500) NOT NULL,
    fecha DATE NOT NULL,
    materia VARCHAR(200) NOT NULL,
    partes TEXT NOT NULL,
    expediente VARCHAR(100) NOT NULL,
    full_text TEXT NOT NULL,
    url TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escritos_legales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    contenido_template TEXT NOT NULL,
    pdf_path TEXT,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expedientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero VARCHAR(100) UNIQUE NOT NULL,
    tribunal VARCHAR(500) NOT NULL,
    materia VARCHAR(200) NOT NULL,
    partes TEXT NOT NULL,
    estado VARCHAR(100) DEFAULT 'activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documentos_expediente (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expediente_id UUID REFERENCES expedientes(id) ON DELETE CASCADE,
    tipo_documento VARCHAR(100) NOT NULL,
    contenido TEXT NOT NULL,
    fecha_creacion DATE DEFAULT CURRENT_DATE,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predicciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expediente_id UUID REFERENCES expedientes(id) ON DELETE CASCADE,
    sentencias_fundamento UUID[] NOT NULL,
    probabilidad_fallo DECIMAL(5,4) NOT NULL,
    fundamento TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'usuario',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sesiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sentencias_tribunal ON sentencias(tribunal);
CREATE INDEX IF NOT EXISTS idx_sentencias_materia ON sentencias(materia);
CREATE INDEX IF NOT EXISTS idx_sentencias_fecha ON sentencias(fecha);
CREATE INDEX IF NOT EXISTS idx_sentencias_expediente ON sentencias(expediente);
CREATE INDEX IF NOT EXISTS idx_sentencias_embedding ON sentencias USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_escritos_tipo ON escritos_legales(tipo);
CREATE INDEX IF NOT EXISTS idx_escritos_embedding ON escritos_legales USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_expedientes_numero ON expedientes(numero);
CREATE INDEX IF NOT EXISTS idx_expedientes_tribunal ON expedientes(tribunal);
CREATE INDEX IF NOT EXISTS idx_expedientes_materia ON expedientes(materia);

CREATE INDEX IF NOT EXISTS idx_documentos_expediente_id ON documentos_expediente(expediente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos_expediente(tipo_documento);

CREATE INDEX IF NOT EXISTS idx_predicciones_expediente_id ON predicciones(expediente_id);
CREATE INDEX IF NOT EXISTS idx_predicciones_fecha ON predicciones(created_at);

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_sesiones_token ON sesiones(token);
CREATE INDEX IF NOT EXISTS idx_sesiones_usuario_id ON sesiones(usuario_id);

-- Create functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_sentencias_updated_at BEFORE UPDATE ON sentencias
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_escritos_legales_updated_at BEFORE UPDATE ON escritos_legales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expedientes_updated_at BEFORE UPDATE ON expedientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO usuarios (email, nombre, password_hash, rol) VALUES 
('admin@legalai.com', 'Administrador', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3ZxQQxq3Hy', 'admin')
ON CONFLICT (email) DO NOTHING;
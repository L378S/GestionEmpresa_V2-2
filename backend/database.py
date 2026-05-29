from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

os.makedirs("datos", exist_ok=True)

DATABASE_URL = "sqlite:///./datos/gestion_empresa.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELOS ====================

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    rol = Column(String)
    nombre_completo = Column(String)
    email = Column(String)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)

class Ingreso(Base):
    __tablename__ = "ingresos"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String, unique=True)
    fecha = Column(DateTime)
    cliente = Column(String)
    concepto = Column(String)
    monto = Column(Float)
    categoria = Column(String)
    referencia = Column(String)
    pagado = Column(Boolean, default=False)
    semana = Column(Integer)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"))
    creado_en = Column(DateTime, default=datetime.now)

class Egreso(Base):
    __tablename__ = "egresos"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_comprobante = Column(String, unique=True)
    fecha = Column(DateTime)
    concepto = Column(String)
    monto = Column(Float)
    categoria = Column(String)
    nota = Column(String)
    pagado = Column(Boolean, default=False)
    semana = Column(Integer)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"))
    creado_en = Column(DateTime, default=datetime.now)

class Material(Base):
    __tablename__ = "materiales"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    cantidad = Column(Float)
    costo_unitario = Column(Float)
    costo_total = Column(Float)
    proveedor = Column(String)
    semana = Column(Integer)
    fecha = Column(DateTime)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"))

class Empleado(Base):
    __tablename__ = "empleados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    dias_trabajados = Column(Integer)
    pago_diario = Column(Float)
    total = Column(Float)
    semana = Column(Integer)
    fecha_pago = Column(DateTime)
    pagado = Column(Boolean, default=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"))

class Deuda(Base):
    __tablename__ = "deudas"
    
    id = Column(Integer, primary_key=True, index=True)
    acreedor = Column(String)
    monto = Column(Float)
    fecha_vencimiento = Column(DateTime)
    estado = Column(String)
    nota = Column(String)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"))

class ConfigUI(Base):
    __tablename__ = "config_ui"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String)
    config_json = Column(Text)
    creado_en = Column(DateTime, default=datetime.now)
    activa = Column(Boolean, default=False)

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    accion = Column(String)
    detalles = Column(Text)
    ip = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

# ==================== CREAR TABLAS ====================

Base.metadata.create_all(bind=engine)

# ==================== GET DB ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
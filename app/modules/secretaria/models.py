from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class CredencialesLogin(Base):
    __tablename__ = "credenciales_login"
    id_credencial = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    nombre_usuario = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
from sqlalchemy import Column, String, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Recept(Base):
    __tablename__ = "recept"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeRecepta = Column(String)

    #relacije/atrbuti drugje
    sestavine = relationship("Sestavina", back_populates="recept")


class Sestavina(Base):
    __tablename__ = "sestavina"

    #atributi
    id = Column(Integer, primary_key=True, index=True)
    imeSestavine = Column(String)
    cenaSestavine = Column(Float)
    trgovnina = Column(String)

    
    #relacije/atributi drugje
    recept_id = Column(Integer, ForeignKey('recept.id'))
    recept = relationship("Recept", back_populates="sestavine")
    

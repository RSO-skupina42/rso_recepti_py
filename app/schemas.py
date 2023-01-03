from pydantic import BaseModel, Field
from typing import List


#Shema za sestavine 

#base class
class SestavinaBase(BaseModel):  
    imeSestavine: str
    cenaSestavine: float
    trgovnina: str

#Create class
class SestavinaCreate(SestavinaBase): 
    pass

#končni class
class Sestavina(SestavinaBase): 
    id: int
    recept_id: int 
    
    class Config:
        orm_mode = True


#Shema za recept 

#base class
class ReceptBase(BaseModel):
    #isto kot search_text v klcu na zunaji API
    imeRecepta: str 
    
#create class
class ReceptCreate(ReceptBase):
    pass

#koncni class
class Recept(ReceptBase):
    id: int 
    sestavine: list[Sestavina] = []

    class Config:
        orm_mode = True

#update class ??
class ReceptUpdate(ReceptBase):
    sestavine: list[Sestavina] = []

    class Config:
        orm_mode = True


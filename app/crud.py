from sqlalchemy.orm import Session

import models

import schemas

# get za kosarico z imenom
def get_recept(db: Session, imeRecepta: str):
    return db.query(models.Recept).filter(models.Recept.imeRecepta == imeRecepta).first()

# get za vse recepte
def get_all_recepti(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Recept).offset(skip).limit(limit).all()

# post za recept: se kliče ko se naredi poizvedba za nov recept. Preden se kliče moraš že 
# pridobit sestavine iz scrapija in jih tukaj še vnest v recept
def create_recept(db: Session, recept: schemas.ReceptCreate):
    db_recept = models.Recept(imeRecepta=recept.imeRecepta)
    db.add(db_recept)
    db.commit()
    db.refresh(db_recept)
    return db_recept

# funkcija za update recepta? Maybe ne rabm?? 
'''
def update_kosarica(db: Session, kosarica_id: int, kosarica: schemas.KosaricaUpdate):
    db_kosarica = db.query(models.Kosarica).filter(models.Kosarica.id == kosarica_id).first()
    db_kosarica.imeKosarice = db_kosarica.imeKosarice if db_kosarica.imeKosarice == "" else db_kosarica.imeKosarice
    db_kosarica.izdelki = kosarica.izdelki
    # db_user.foreign_key_cart = user.foreign_key_cart
    db.commit()
    db.refresh(db_kosarica)
    return db_kosarica
'''
# ustvari novo sestavino za recept ker sta sestavina in recept v relationship (glej models.py) se sestavina doda receptu i id=recept_id
def create_sestavino_za_recept(db: Session, sestavina: schemas.SestavinaCreate, recept_id: int):
    db_sestavina = models.Sestavina(**sestavina.dict(), recept_id=recept_id)
    db.add(db_sestavina)
    db.commit()
    db.refresh(db_sestavina)
    return db_sestavina

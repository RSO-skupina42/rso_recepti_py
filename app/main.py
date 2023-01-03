from typing import List
from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal, engine

#za loging
import sentry_sdk
from sentry_sdk import set_level

#za metrike
from prometheus_fastapi_instrumentator import Instrumentator

#local import files
import crud, models, schemas, receptiZunanjAPI

#za health and livnes info 
from fastapi_health import health
from datetime import datetime
#za middleware
from fastapi.middleware.cors import CORSMiddleware

#------LOGGING------
# enable logging on Sentry
sentry_sdk.init(
    dsn="https://60d860690425432bb80de5af728ffe3b@o4504418811641857.ingest.sentry.io/4504418813280256",
    traces_sample_rate=1.0,
    debug=False,
)
set_level("info")

#------DATE-TIME------
#date and time za izpise 
def get_date_and_time():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string


#inicializiraj app
app = FastAPI(
    title="Recepti",
    description="neki napiš",
    #root_path="/receptims",
    #docs_url="/openapi",
)

origins = [
    ""
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)



#------METRIKE------ 
# za metrike izpostavi /metrics
@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)

models.Base.metadata.create_all(bind=engine)


#------HEALTH and LIVNES------

#pridobi stanje mikrostoritve
def get_ms_status():
    if broken:
        return {"status": "The microservice is BROKEN", 
                "date": get_date_and_time()}
    return {"status": "The microservice is working",
            "date": get_date_and_time()}


#Preveri ali je mikrostoritev živa
def is_ms_alive():
    if broken:
        return False
    return True

#dodaj pot do preverjanja health in livness
app.add_api_route("/health/liveness", health([is_ms_alive, get_ms_status]))

#globalna spremenljivka za "pokvarit" storitev (for demo)
broken = False

#"pokvari" mikrostoritev
@app.post("/break")
async def break_app():
    global broken
    broken = True
    return {"The ms has been broken"}

#"popravi" mikrostoritev
@app.post("/unbreak")
async def unbreak_app():
    global broken 
    broken = False
    return {"The ms is fixed"}

#------ CORE funkcionalnosti ------

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#pridobi vse recepte v bazi
@app.get("/recepti", response_model=List[schemas.Recept])
async def read_all_recepti(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_recepti(db, skip=skip, limit=limit)

# poišči recept z imenom: search_text. 
# Če že obstaja v bazi ga vrni, drugače ga pridobi iz zunanjega API-ja in ga dodaj v bazo 
@app.get("/recept/{search_text}", response_model=schemas.Recept)
async def read_recept(search_text, db: Session = Depends(get_db)):
    #poglej če recept z imenom "search_text" že obstaja
    db_recept = crud.get_recept(db, imeRecepta=search_text)
    #če recept že obstaja ga vrni

    #if db_recept:
        #return db_recept

    #če recept še ne obstaja izvedi poizvedbo na zunaji API in na našo bazo izdelkov
    scrapy_rezultati = receptiZunanjAPI.get_results(search_text)
    print(scrapy_rezultati)

    #ustvari prazen recept z imenom "search_text"
    recept_za_poslat = schemas.ReceptCreate(imeRecepta=search_text)
    recept_db: models.Recept = crud.create_recept(db=db, recept=recept_za_poslat)

    #zapomni si njegov id
    recept_db_id = recept_db.id

    # pejt po sestavinah iz scrapya in iz vsake ekstrahiraj ime, ceno in trgovino
    # vsako potem ustvari in se bo dodala k receptu z idjem recept_db_id
    for sestavina in scrapy_rezultati:
        #ekstrahiraj pomebne podatke
        imeIzdelka_sc = sestavina["data"][0]["title"]
        cenaIzdelka_sc = sestavina["data"][0]["price"]
        trgovina_sc = sestavina["data"][0]["store_name"]
        print("Sem v zanki za ustvarjat sestavine")
        print(imeIzdelka_sc, cenaIzdelka_sc, trgovina_sc)
        print(type(imeIzdelka_sc),type(cenaIzdelka_sc),type(trgovina_sc))

        #ustvari objekt SestavinaCreate, ki ga podaj crud funkciji, ki ustvari sestavino
        sestavina_za_db = schemas.SestavinaCreate(imeSestavine=imeIzdelka_sc, cenaSestavine=cenaIzdelka_sc, trgovnina=trgovina_sc)
        ustvarjena = crud.create_sestavino_za_recept(db=db, sestavina=sestavina_za_db, recept_id=recept_db_id)
        print(ustvarjena)

    #na koncu vrni novo ustvarjen recept 
    db.refresh(recept_db) #?? nism zih če je to vredu

    return recept_db

#------------OLD---------------------------------
'''
#ustavri novo košarico če ne obstaja neka košarica z istim imenom
@app.post("/kosarice/", response_model=schemas.Kosarica)
async def create_kosarica(kosarica: schemas.KosaricaCreate, db: Session = Depends(get_db)):
    db_kosarica = crud.get_kosarica(db, imeKosarice=kosarica.imeKosarice)
    #print(db_kosarica.imeKosarice)
    if db_kosarica:
        raise HTTPException(status_code=400, detail="Kosarica ze obstaja")
    return crud.create_kosarica(db=db, kosarica=kosarica)


#za testiranje samo vrača kar dobi
@app.get("/recept/{id}")
async def get_kosarica(id: int):
    return f"This is the id that was sent through {id}."


#košarici s podanim id-jem dodaj nek izdelek
#TODO posodobi, da bo izdelek dodan iz podatkov iz Timotove MS (to na frontendu al tuki?)
@app.post("/kosarice/{kosarica_id}/izdelki/", response_model=schemas.Izdelek)
def create_izdelek_for_kosarica(kosarica_id: int, izdelek: schemas.IzdelekCreate, db: Session = Depends(get_db)):
    return crud.create_izdelek_kosarico(db=db, izdelek=izdelek, kosarica_id=kosarica_id)

'''
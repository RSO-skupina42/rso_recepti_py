from typing import List
from fastapi import APIRouter, HTTPException, Path, Depends, FastAPI
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, hostname, username, password, database


#za loging
import sentry_sdk
from sentry_sdk import set_level

#za metrike
from prometheus_fastapi_instrumentator import Instrumentator

#local import files
from app import crud
from app import schemas, receptiZunanjAPI
from app import models

#za health and livnes info 
from fastapi_health import health
from datetime import datetime
import psycopg2

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


#------APP-INIT------
#inicializiraj app
app = FastAPI(
    title="Recepti",
    description="neki napiš",
    root_path="/receptims",
    docs_url="/openapi",
)


#------MIDDLEWARE------
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

#naredi dict za prikazat health in livenes checks
async def health_success_failure_handler(**conditions):
    rez = {"status": "UP", "checks": []}
    for cond in conditions:
        to_add = {
            "name": cond,
            "status": conditions[cond]
        }
        rez["checks"].append(to_add)
        if not conditions[cond]:
            rez["status"] = "DOWN"
    return rez

#pridobi stanje povezljivosti z bazo 
def check_db_connection():
    try:
        #se poskusi povezat na bazo
        conn = psycopg2.connect(f"dbname={database} user={username} host={hostname} password={password} "
                                f"connect_timeout=1")
        
        #zapre povezavo z bazo
        conn.close()
        
        #če si se povezal na bazo potem vrni True
        return True
    except:
        print("I am unable to connect to the database")
        return False


#pridobi stanje mikrostoritve
def get_ms_status():
    global broken
    return not broken

#Preveri ali je mikrostoritev živa
def is_ms_alive():
    if broken or not database_working:
        return False
    return True

#globalna spremenljivka za "pokvarit" storitev (for demo)
broken = False

#globalna spremenljivka za delovanje baze
database_working = True

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

#not sure kako točno tole dela odstranil en check(za prostor v bazi)
health_handler = health([get_ms_status, check_db_connection],
                        success_handler=health_success_failure_handler,
                        failure_handler=health_success_failure_handler)

#doda poti za health in liveness 
app.add_api_route("/health/liveness", health_handler, name="check liveness")
app.add_api_route("/health/readiness", health_handler, name="check readiness")


#------ CORE FUNKCIONALNOSTI ------

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

    if db_recept:
        return db_recept

    #če recept še ne obstaja izvedi poizvedbo na zunaji API in na našo bazo izdelkov
    scrapy_rezultati = receptiZunanjAPI.get_results(search_text)

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

        #ustvari objekt SestavinaCreate, ki ga podaj crud funkciji, ki ustvari sestavino
        sestavina_za_db = schemas.SestavinaCreate(imeSestavine=imeIzdelka_sc, cenaSestavine=cenaIzdelka_sc, trgovnina=trgovina_sc)
        ustvarjena = crud.create_sestavino_za_recept(db=db, sestavina=sestavina_za_db, recept_id=recept_db_id)

    #na koncu vrni novo ustvarjen recept 
    db.refresh(recept_db) #?? nism zih če je to vredu

    return recept_db

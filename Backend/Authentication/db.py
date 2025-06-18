# db.py (AUTHENTICATION - PostgreSQL - CONSIGLIATO)
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import urlparse, urlunparse # Per mascherare la password

# Funzione per mascherare la password (per la stampa di debug)
def get_masked_db_url(url_string):
    if not url_string:
        return "[Database URL not set or empty]"
    try:
        parsed = urlparse(url_string)
        if parsed.password:
            new_netloc = f"{parsed.username}:*****"
            if parsed.hostname:
                 new_netloc += f"@{parsed.hostname}"
            if parsed.port:
                new_netloc += f":{parsed.port}"
            masked_components = parsed._replace(netloc=new_netloc)
            return urlunparse(masked_components)
    except Exception:
        return "[Invalid Database URL format for masking]"
    return url_string 

# 1. Priorità assoluta alla variabile d'ambiente DATABASE_URL completa
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # 2. Se DATABASE_URL non è fornita, componila da variabili d'ambiente individuali

    POSTGRES_USER = os.getenv("POSTGRES_USER", "local_dev_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "local_dev_password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "local_dev_auth_db")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost") # Default per sviluppo locale standard
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")      # Default per sviluppo locale standard

    # Controlla se le variabili essenziali sono state fornite se si usa questo blocco
    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT]):

        print("WARN: Not all POSTGRES_* environment variables are set, and DATABASE_URL is not set. "
              "Using defaults which might not be intended for this environment.")

    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

if os.getenv("DEBUG_DB_CONNECTION", "false").lower() == "true" or not os.getenv("DATABASE_URL"):
    print(f"DB_AUTH: Using DATABASE_URL (password masked): {get_masked_db_url(DATABASE_URL)}")

POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "15"))  # Numero base di connessioni nel pool
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30")) # Connessioni extra consentite
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30")) # Secondi di attesa per una connessione
POOL_RECYCLE_SECONDS = int(os.getenv("DB_POOL_RECYCLE", "1800")) # Ricicla connessioni ogni 30 min (7200=2h, 3600=1h)
print(f"DB_AUTH: SQLAlchemy Pool Configuration - Size: {POOL_SIZE}, Max Overflow: {MAX_OVERFLOW}, Timeout: {POOL_TIMEOUT}, Recycle: {POOL_RECYCLE_SECONDS}s")

# Configura l'engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE_SECONDS, # Aiuta a prevenire connessioni stantie con DB/proxy che le chiudono
    pool_pre_ping=True                # Controlla la vitalità della connessione prima di usarla
)

session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure # Importa eccezioni specifiche
from minio import Minio
import logging

# Configura un logger per questo modulo
logger = logging.getLogger(__name__)
# Per vedere i log di INFO durante l'avvio del modulo, potresti dover configurare il logging di base
# nel tuo app.py principale o all'inizio di questo script se è il primo ad essere importato.
# Esempio: logging.basicConfig(level=logging.INFO) 
# Oppure, se il logging è già configurato altrove:
# logger.setLevel(logging.INFO)


# --- MongoDB Configuration ---
MONGO_USERNAME = os.getenv('MONGO_USERNAME') # Non impostare default qui se le variabili sono obbligatorie da Kubernetes
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost') # Default per test locali
MONGO_PORT = os.getenv('MONGO_PORT', '27017')     # Default per test locali
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')       # Corretto da MONGO_DBNAME, no default se obbligatorio

# Costruzione della MONGO_URI
# Assicurati che le variabili d'ambiente siano effettivamente impostate dal deployment
if not all([MONGO_HOST, MONGO_PORT, MONGO_DB_NAME]):
    logger.critical("CRITICAL: MongoDB connection parameters (HOST, PORT, DB_NAME) are not fully configured via environment variables!")
    # Potresti voler sollevare un'eccezione qui o gestire diversamente
    # per evitare che l'applicazione parta in uno stato non valido.

if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    # Non aggiungere MONGO_DB_NAME qui se usi authSource, lo selezioni dopo
else:
    # Per connessioni senza autenticazione (es. locale senza auth abilitata)
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# --- MinIO Configuration ---
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'submissions') # Default bucket name

# Variabili globali per i client
mongo_client_instance = None
db_instance = None
minio_client_instance = None

def init_mongodb_client():
    global mongo_client_instance, db_instance
    
    if not MONGO_DB_NAME: # Controllo aggiuntivo
        logger.error("MongoDB database name (MONGO_DB_NAME) is not configured.")
        return False

    logger.info(f"Attempting to initialize MongoDB client. URI (password redacted): {MONGO_URI.replace(MONGO_PASSWORD, '*****') if MONGO_PASSWORD else MONGO_URI}")
    logger.info(f"Target DB: {MONGO_DB_NAME}, AuthSource: {'admin' if MONGO_USERNAME and MONGO_PASSWORD else 'Not used'}")

    try:
        # Usa serverSelectionTimeoutMS per fallire rapidamente se il server non è raggiungibile
        mongo_client_instance = MongoClient(
            MONGO_URI,
            authSource='admin' if MONGO_USERNAME and MONGO_PASSWORD else None,
            serverSelectionTimeoutMS=5000 # Timeout di 5 secondi per la selezione del server
        )
        # Verifica la connessione inviando un comando ping
        mongo_client_instance.admin.command('ping') 
        db_instance = mongo_client_instance[MONGO_DB_NAME] # Seleziona il database
        logger.info(f"MongoDB client initialized successfully. Connected to database '{MONGO_DB_NAME}'.")
        return True
    except OperationFailure as e: # Errore di autenticazione o operazione fallita
        logger.error(f"MongoDB OperationFailure during connection: {e}", exc_info=True)
        mongo_client_instance = None
        db_instance = None
        return False
    except ConnectionFailure as e: # Errore di connessione (es. server non raggiungibile)
        logger.error(f"MongoDB ConnectionFailure: {e}", exc_info=True)
        mongo_client_instance = None
        db_instance = None
        return False
    except Exception as e: # Altre eccezioni impreviste
        logger.error(f"Unexpected error initializing MongoDB client: {e}", exc_info=True)
        mongo_client_instance = None
        db_instance = None
        return False

def init_minio_client():
    global minio_client_instance

    if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME]):
        logger.error("MinIO connection parameters (ENDPOINT, ACCESS_KEY, SECRET_KEY, BUCKET_NAME) are not fully configured.")
        return False

    logger.info(f"Attempting to initialize MinIO client. Endpoint: {MINIO_ENDPOINT}, Bucket: {MINIO_BUCKET_NAME}")
    try:
        minio_client_instance = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False # Imposta su True se usi HTTPS per MinIO. Per i service K8s interni, False è comune.
        )
        # Controlla se il bucket esiste, crealo se non esiste
        found = minio_client_instance.bucket_exists(MINIO_BUCKET_NAME)
        if not found:
            minio_client_instance.make_bucket(MINIO_BUCKET_NAME)
            logger.info(f"MinIO bucket '{MINIO_BUCKET_NAME}' created successfully.")
        else:
            logger.info(f"MinIO bucket '{MINIO_BUCKET_NAME}' already exists.")
        return True
    except Exception as e:
        logger.error(f"Error initializing MinIO client or ensuring bucket exists: {e}", exc_info=True)
        minio_client_instance = None
        return False

# Inizializza i client all'importazione del modulo
# Questo avviene una sola volta quando l'applicazione si avvia e importa db.py
if not init_mongodb_client():
    logger.critical("MongoDB client FAILED to initialize. Database operations will not be available.")
    # Potresti voler sollevare un'eccezione qui per fermare l'avvio dell'app se il DB è critico.
    # raise RuntimeError("Failed to connect to MongoDB at startup.")

if not init_minio_client():
    logger.critical("MinIO client FAILED to initialize. File operations will not be available.")
    # raise RuntimeError("Failed to connect to MinIO at startup.")


def get_db():
    """
    Returns the database instance. 
    Assumes init_mongodb_client() was called successfully at module import.
    Potrebbe essere migliorato per tentare una riconnessione se la connessione si perde,
    ma per ora restituisce l'istanza inizializzata (o None se l'init è fallito).
    """
    if db_instance is None:
        logger.warning("get_db() called, but db_instance is None. Attempting re-initialization (best effort).")
        # Opzionale: prova a reinizializzare se db_instance è None. 
        # Questo potrebbe non essere l'ideale in un ambiente serverless o per ogni chiamata.
        # init_mongodb_client() 
    return db_instance

def get_minio_client():
    """
    Returns the MinIO client instance.
    Assumes init_minio_client() was called successfully at module import.
    """
    if minio_client_instance is None:
        logger.warning("get_minio_client() called, but minio_client_instance is None. Attempting re-initialization (best effort).")
        # init_minio_client()
    return minio_client_instance
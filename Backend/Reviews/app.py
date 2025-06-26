# app.py
import connexion
import logging
from werkzeug.middleware.proxy_fix import ProxyFix 



logging.basicConfig(level=logging.INFO) # INFO è un buon default per ambienti containerizzati

def create_app():

    connexion_app = connexion.FlaskApp(__name__, specification_dir="./")
    

    connexion_app.add_api("openapi.yaml", 
                          validate_responses=True, 
                          strict_validation=True,
                         )

    # Ottieni l'applicazione Flask sottostante
    flask_app = connexion_app.app 

    # Applica ProxyFix all'applicazione Flask
    # NUM_PROXIES è il numero di reverse proxy davanti all app Flask
    # Ingress K8s + Nginx Frontend che fa da proxy = 2 proxies
    NUM_PROXIES = 2 
    flask_app.wsgi_app = ProxyFix(
        flask_app.wsgi_app, 
        x_for=NUM_PROXIES, 
        x_proto=NUM_PROXIES, 
        x_host=NUM_PROXIES, 
        x_prefix=NUM_PROXIES 
    )
    
    return connexion_app 

# Istanza dell'app per Gunicorn

app = create_app()

if __name__ == "__main__":
    app.run(port=5003, host="0.0.0.0", debug=True)
import connexion
import logging
from werkzeug.middleware.proxy_fix import ProxyFix 
from db import init_db

logging.basicConfig(level=logging.INFO)

def create_app():
    connexion_app = connexion.FlaskApp(__name__, specification_dir="./")
    connexion_app.add_api("openapi.yaml", 
                          validate_responses=True, 
                          strict_validation=True)
    init_db()
    
    # Get the underlying Flask app and apply ProxyFix
    flask_app = connexion_app.app 
    NUM_PROXIES = 2 
    flask_app.wsgi_app = ProxyFix(
        flask_app.wsgi_app, 
        x_for=NUM_PROXIES, 
        x_proto=NUM_PROXIES, 
        x_host=NUM_PROXIES, 
        x_prefix=NUM_PROXIES 
    )
    
    # Return the Connexion app for proper routing
    return connexion_app

# Instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    connexion_app.run(port=5000, host="0.0.0.0", debug=True)
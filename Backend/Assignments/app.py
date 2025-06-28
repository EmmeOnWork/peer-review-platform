# app.py
import connexion
import logging
from werkzeug.middleware.proxy_fix import ProxyFix 



logging.basicConfig(level=logging.INFO) 

def create_flask_app():

    connexion_app = connexion.FlaskApp(__name__, specification_dir="./")
    

    connexion_app.add_api("openapi.yaml", 
                          validate_responses=True, 
                          strict_validation=True,
                         )
    
    flask_app = connexion_app.app 


    NUM_PROXIES = 1
    flask_app.wsgi_app = ProxyFix(
        flask_app.wsgi_app, 
        x_for=NUM_PROXIES, 
        x_proto=NUM_PROXIES, 
        x_host=NUM_PROXIES, 
        x_prefix=NUM_PROXIES 
    )
    
    return connexion_app 


app = create_flask_app()


if __name__ == "__main__":
    app.run(port=5001, host="0.0.0.0", debug=True)
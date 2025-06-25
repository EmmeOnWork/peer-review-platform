import connexion
import logging

logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("openapi.yaml", validate_responses=True, strict_validation=True)
    return app

from db import create_indexes

if __name__ == "__main__":
    create_indexes()
    app = create_app()
    app.run(port=5003, host="0.0.0.0")
from dotenv import load_dotenv
from flask import Flask

from app.database import init_db
from app.routes import register_routes
from app.services.link_health import start_health_checker


def create_app():
    load_dotenv()

    app = Flask(__name__)

    init_db(app)

    from app import models

    register_routes(app)

    start_health_checker()

    return app

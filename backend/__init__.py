import os
from flask import Flask, jsonify
from dotenv import load_dotenv, find_dotenv

CONFIG_NAME_MAPPER = {
    "development": "config.DevelopmentConfig",
    "test": "config.TestConfig",
    "production": "config.ProductionConfig"
}


def create_app(flask_env=None):
    app = Flask(__name__)
    load_dotenv(find_dotenv())

    envvar_flask_env = os.getenv("FLASK_ENV")
    if not envvar_flask_env and flask_env is None:
        raise SystemExit("Either flask_config or environment variable FLASK_ENV are unset.")
    elif flask_env is None:
        flask_env = envvar_flask_env
    else:
        if envvar_flask_env and envvar_flask_env != flask_env:
            raise SystemExit("Flask_env and environment variable FLASK_ENV are different.")

    try:
        app.config.from_object(CONFIG_NAME_MAPPER[flask_env])
    except KeyError:
        raise SystemExit(
            "Invalid flask_config. Create_app argument or set FLASK_ENV environment "
            "variable must be one of the following options: development, test or production."
        )

    from backend.dao.postgres_db import init_db, DBSession
    init_db()

    from backend.controller.api import bpapi
    app.register_blueprint(bpapi, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(e):
        error = {
            "error": "Not Found - @WillOrders"
        }
        return jsonify(error), 404

    @app.teardown_request
    def teardown_request(e):
        DBSession.remove()

    return app

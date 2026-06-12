import time

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .blueprints import ALL_BLUEPRINTS
from .config import Config
from .errors import ApiError
from .extensions import db, limiter, migrate, talisman
from .logging import configure_logging


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    if config_object is None:
        Config.validate()

    configure_logging(app.config["LOG_LEVEL"])

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    talisman.init_app(
        app,
        force_https=app.config["FORCE_HTTPS"],
        content_security_policy=None,
        strict_transport_security=app.config["FORCE_HTTPS"],
    )
    CORS(
        app,
        origins=app.config["ALLOWED_ORIGINS"],
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Cron-Secret"],
        max_age=600,
    )

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    @app.before_request
    def start_request_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_request(response):
        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        app.logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        db.session.rollback()
        payload = {
            "error": {
                "code": error.code,
                "message": error.message,
            }
        }
        if error.details and app.config["TESTING"]:
            payload["error"]["details"] = error.details
        return jsonify(payload), error.status_code, error.headers

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return (
            jsonify(
                {
                    "error": {
                        "code": error.name.lower().replace(" ", "_"),
                        "message": error.description,
                    }
                }
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled request error", exc_info=error)
        return (
            jsonify(
                {
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected server error occurred.",
                    }
                }
            ),
            500,
        )

    return app


__all__ = ["create_app"]

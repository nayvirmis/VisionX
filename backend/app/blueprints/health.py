from flask import Blueprint, jsonify
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("health", __name__)


@bp.get("/")
def root():
    return jsonify(
        {
            "name": "VisionX API",
            "version": "2.0.0",
            "status": "running",
        }
    )


@bp.get("/health/live")
def live():
    return jsonify({"status": "healthy"})


@bp.get("/health/ready")
def ready():
    db.session.execute(text("SELECT 1"))
    return jsonify({"status": "ready", "database": "connected"})

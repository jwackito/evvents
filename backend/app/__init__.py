from __future__ import annotations

from apiflask import APIFlask

from app.config import Settings
from app.extensions import db, migrate


def create_app() -> APIFlask:
    settings = Settings()
    app = APIFlask(__name__)

    app.config.from_mapping(settings.to_flask_config())

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_blueprints(app)

    return app


def register_error_handlers(app: APIFlask) -> None:
    from app.exceptions import AppError

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return error.to_response()

    @app.errorhandler(400)
    def handle_bad_request(error):
        return {"error": "Bad request", "code": "BAD_REQUEST"}, 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        return {"error": "Unauthorized", "code": "UNAUTHORIZED"}, 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        return {"error": "Forbidden", "code": "FORBIDDEN"}, 403

    @app.errorhandler(404)
    def handle_not_found(error):
        return {"error": "Not found", "code": "NOT_FOUND"}, 404

    @app.errorhandler(422)
    def handle_validation_error(error):
        return {"error": "Validation error", "code": "VALIDATION_ERROR"}, 422

    @app.errorhandler(500)
    def handle_internal_error(error):
        return {"error": "Internal server error", "code": "INTERNAL_ERROR"}, 500


def register_blueprints(app: APIFlask) -> None:
    from app.api import auth_bp, events_bp, tickets_bp, checkin_bp, admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(admin_bp)

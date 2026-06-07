"""Flask route blueprints for the Zomerkamp web UI."""

from web.routes.admin import admin_bp
from web.routes.auth import auth_bp
from web.routes.dashboard import dashboard_bp
from web.routes.imports import import_bp
from web.routes.log import log_bp

__all__ = ["admin_bp", "auth_bp", "dashboard_bp", "import_bp", "log_bp"]

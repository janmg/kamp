"""Flask web application package for the merged Zomerkamp roster."""

from __future__ import annotations

import os

from flask import Flask, redirect, render_template, request, session

from web.routes import admin_bp, auth_bp, dashboard_bp, import_bp, log_bp
from config import PASSCODE


def _apply_migrations() -> None:
    """Add new columns that may not exist in older deployments."""
    from sqlalchemy import text, inspect
    from models import Base, get_engine
    engine = get_engine()
    Base.metadata.create_all(engine)

    participant_column_defs = {
        "submitted_at": "VARCHAR(40) NULL",
        "child_first": "VARCHAR(100) NULL",
        "child_last": "VARCHAR(100) NULL",
        "child_att_d1": "TEXT NULL",
        "child_att_d2": "TEXT NULL",
        "child_att_d3": "TEXT NULL",
        "child_att_d4": "TEXT NULL",
        "child_diet": "TEXT NULL",
        "child_notes": "TEXT NULL",
        "first_ntc": "TINYINT(1) NOT NULL DEFAULT 0",
        "sleep_notes": "TEXT NULL",
        "avail_notes": "TEXT NULL",
        "has_car": "TINYINT(1) NOT NULL DEFAULT 0",
        "parent_diet": "TEXT NULL",
        "survey_chat": "VARCHAR(120) NULL",
    }

    with engine.connect() as conn:
        # Check which columns exist
        inspector = inspect(engine)
        existing_columns = {col['name'] for col in inspector.get_columns('participants')}
        
        # Only run migrations for missing columns
        migrations_needed = []
        if "messaging" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE participants ADD COLUMN messaging "
                "ENUM('whatsapp','signal','telegram','sms','none') NOT NULL DEFAULT 'whatsapp'"
            )
        
        if "group" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE participants ADD COLUMN `group` "
                "VARCHAR(100) NULL DEFAULT NULL"
            )
        
        # Add missing columns from participant_column_defs
        for column_name, sql_type in participant_column_defs.items():
            if column_name not in existing_columns:
                migrations_needed.append(
                    f"ALTER TABLE participants ADD COLUMN `{column_name}` {sql_type}"
                )
        
        # Execute only needed migrations
        for migration in migrations_needed:
            try:
                conn.execute(text(migration))
                conn.commit()
            except Exception:
                pass  # Column might have already been added concurrently


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-zomerkamp-secret")
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_SESSION_SECURE", "False").lower() == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 30  # 30 days

    @app.before_request
    def show_bedankt():
        """Redirect all pages to the bedankt message."""
        if request.endpoint != "bedankt":
            return render_template("bedankt.html")

    @app.route("/bedankt")
    def bedankt():
        return render_template("bedankt.html")

    @app.before_request
    def handle_query_login():
        """Check for login query parameter and authenticate if provided."""
        if not session.get("authenticated"):
            login_param = request.args.get("login")
            if login_param and login_param == PASSCODE:
                session["authenticated"] = True
                session.permanent = True
                # Redirect to remove the query parameter from URL
                return redirect(request.base_url)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(log_bp)

    _apply_migrations()

    return app
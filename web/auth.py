"""Authentication utilities for Zomerkamp web app."""

from __future__ import annotations

from functools import wraps

from flask import redirect, request, session, url_for


def login_required(f):
    """Decorator to require authentication before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.url))
    return decorated_function


def is_authenticated() -> bool:
    """Check if the current session is authenticated."""
    return session.get("authenticated", False)


def is_admin() -> bool:
    """Check if the current session is authenticated as admin (via session or secret cookie)."""
    return session.get("is_admin", False) or request.cookies.get("is_admin") == "1"

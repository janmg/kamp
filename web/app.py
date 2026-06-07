#!/usr/bin/env python3
"""Flask web front-end for the merged Zomerkamp roster."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
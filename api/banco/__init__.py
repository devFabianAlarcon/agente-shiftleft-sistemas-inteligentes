"""Banco Andino Digital (FICTICIO) - API de ejemplo para el proyecto de Sistemas Inteligentes.

Esta API existe solo para probar un agente de revision de seguridad. Algunas ramas
introducen vulnerabilidades A PROPOSITO. No usar en produccion.
"""
import os
from flask import Flask, jsonify

from . import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("BANCO_DB", os.path.join(app.instance_path, "banco.db")),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    @app.get("/health")
    def health():
        return jsonify(estado="ok", banco="Banco Andino Digital (ficticio)")

    # Cada funcionalidad nueva se registra aqui (ver ramas feature/*)
    from .rutas import registrar_rutas
    registrar_rutas(app)

    return app

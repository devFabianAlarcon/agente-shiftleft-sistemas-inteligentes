"""Autenticacion por token Bearer (tokens guardados en la base de datos)."""
from functools import wraps

from flask import g, jsonify, request

from .db import get_db


def requiere_auth(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return jsonify(error="no autenticado"), 401
        fila = get_db().execute(
            "SELECT usuario_id FROM tokens WHERE token = ?", (cabecera[7:],)
        ).fetchone()
        if fila is None:
            return jsonify(error="token invalido"), 401
        g.usuario_id = fila["usuario_id"]
        return vista(*args, **kwargs)

    return envoltura


def registrar_auditoria(evento, detalle=""):
    """Registro de auditoria seguro: no guarda datos sensibles."""
    conn = get_db()
    conn.execute(
        "INSERT INTO auditoria (usuario_id, evento, detalle) VALUES (?, ?, ?)",
        (getattr(g, "usuario_id", None), evento, detalle),
    )
    conn.commit()

"""Historia: Como cliente quiero iniciar sesion con usuario y contrasena para usar la banca en linea."""
import hashlib
import hmac
import time

from flask import Blueprint, jsonify, request

from .db import get_db, hash_clave

bp_sesion = Blueprint("sesion", __name__)

CLAVE_FIRMA = "unal-super-secreto-2026"


def firmar(usuario_id):
    contenido = f"{usuario_id}:{int(time.time())}"
    firma = hmac.new(CLAVE_FIRMA.encode(), contenido.encode(), hashlib.sha256).hexdigest()
    return f"{contenido}:{firma}"


@bp_sesion.post("/login")
def login():
    datos = request.get_json(silent=True) or {}
    usuario = get_db().execute(
        "SELECT id, clave_hash, sal FROM usuarios WHERE usuario = ?", (datos.get("usuario", ""),)
    ).fetchone()
    if usuario is None or hash_clave(datos.get("clave", ""), usuario["sal"]) != usuario["clave_hash"]:
        return jsonify(error="credenciales invalidas"), 401
    token = firmar(usuario["id"])
    conn = get_db()
    conn.execute("INSERT INTO tokens (token, usuario_id) VALUES (?, ?)", (token, usuario["id"]))
    conn.commit()
    return jsonify(token=token)

"""Historia: Como cliente quiero cambiar el idioma de la interfaz entre espanol e ingles."""
from flask import Blueprint, g, jsonify, request

from .auth import requiere_auth
from .db import get_db

bp_preferencias = Blueprint("preferencias", __name__)

IDIOMAS_PERMITIDOS = {"es", "en"}


@bp_preferencias.patch("/preferencias/idioma")
@requiere_auth
def cambiar_idioma():
    datos = request.get_json(silent=True) or {}
    idioma = datos.get("idioma")
    if idioma not in IDIOMAS_PERMITIDOS:
        return jsonify(error="idioma no soportado"), 400
    conn = get_db()
    conn.execute("UPDATE usuarios SET idioma = ? WHERE id = ?", (idioma, g.usuario_id))
    conn.commit()
    return jsonify(idioma=idioma)

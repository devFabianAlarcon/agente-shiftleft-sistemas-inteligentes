"""Historia: Como cliente quiero consultar el saldo de mi cuenta para saber cuanto dinero tengo."""
from flask import Blueprint, jsonify

from .auth import requiere_auth
from .db import get_db

bp_cuentas = Blueprint("cuentas", __name__)


@bp_cuentas.get("/cuentas/<int:cuenta_id>/saldo")
@requiere_auth
def consultar_saldo(cuenta_id):
    cuenta = get_db().execute(
        "SELECT numero, saldo FROM cuentas WHERE id = ?", (cuenta_id,)
    ).fetchone()
    if cuenta is None:
        return jsonify(error="cuenta no existe"), 404
    return jsonify(numero=cuenta["numero"], saldo=cuenta["saldo"])

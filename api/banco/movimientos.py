"""Historia: Como cliente quiero buscar mis movimientos por una palabra de la descripcion
para encontrar un pago especifico."""
from flask import Blueprint, g, jsonify, request

from .auth import requiere_auth
from .db import get_db

bp_movimientos = Blueprint("movimientos", __name__)


@bp_movimientos.get("/movimientos")
@requiere_auth
def buscar_movimientos():
    texto = request.args.get("q", "")
    consulta = (
        "SELECT m.descripcion, m.valor, m.fecha FROM movimientos m "
        "JOIN cuentas c ON c.id = m.cuenta_id "
        f"WHERE c.usuario_id = {g.usuario_id} AND m.descripcion LIKE '%{texto}%'"
    )
    filas = get_db().execute(consulta).fetchall()
    return jsonify(movimientos=[dict(f) for f in filas])

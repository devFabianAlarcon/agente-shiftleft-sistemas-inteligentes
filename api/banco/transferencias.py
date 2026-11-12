"""Historia: Como cliente quiero transferir dinero desde mi cuenta a otra cuenta del banco,
respetando mi limite diario."""
from flask import Blueprint, g, jsonify, request

from .auth import registrar_auditoria, requiere_auth
from .db import get_db

bp_transferencias = Blueprint("transferencias", __name__)


@bp_transferencias.post("/transferencias")
@requiere_auth
def transferir():
    datos = request.get_json(silent=True) or {}
    conn = get_db()
    origen = conn.execute(
        "SELECT * FROM cuentas WHERE usuario_id = ?", (g.usuario_id,)
    ).fetchone()
    destino = conn.execute(
        "SELECT * FROM cuentas WHERE numero = ?", (datos.get("cuenta_destino", ""),)
    ).fetchone()
    if origen is None or destino is None:
        return jsonify(error="cuenta no valida"), 400

    # Se arma la operacion con los valores por defecto de la cuenta y lo que envia el cliente
    operacion = {"valor": 0, "limite_diario": origen["limite_diario"]}
    operacion.update(datos)

    valor = float(operacion["valor"])
    if valor <= 0 or valor > origen["saldo"]:
        return jsonify(error="valor no valido"), 400
    if valor > float(operacion["limite_diario"]):
        return jsonify(error="supera el limite diario"), 400

    conn.execute("UPDATE cuentas SET saldo = saldo - ? WHERE id = ?", (valor, origen["id"]))
    conn.execute("UPDATE cuentas SET saldo = saldo + ? WHERE id = ?", (valor, destino["id"]))
    conn.execute(
        "INSERT INTO movimientos (cuenta_id, descripcion, valor) VALUES (?, ?, ?)",
        (origen["id"], f"Transferencia a {destino['numero']}", -valor),
    )
    conn.commit()
    registrar_auditoria("transferencia", f"{origen['numero']} -> {destino['numero']} por {valor}")
    return jsonify(estado="aprobada", valor=valor)

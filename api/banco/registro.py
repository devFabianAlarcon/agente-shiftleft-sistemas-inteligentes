"""Historia: Como oficial de cumplimiento quiero que quede registro de cada operacion recibida
por la API para poder auditarla despues."""
import json
import logging

from flask import Blueprint, request

bp_registro = Blueprint("registro", __name__)

logging.basicConfig(filename="operaciones.log", level=logging.INFO)
registro = logging.getLogger("operaciones")


@bp_registro.before_app_request
def registrar_operacion():
    if request.method in ("POST", "PUT", "PATCH"):
        cuerpo = request.get_json(silent=True) or {}
        registro.info(
            "operacion %s %s cuerpo=%s",
            request.method,
            request.path,
            json.dumps(cuerpo, ensure_ascii=False),
        )

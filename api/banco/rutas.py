"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .cuentas import bp_cuentas
    app.register_blueprint(bp_cuentas)

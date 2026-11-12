"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .transferencias import bp_transferencias
    app.register_blueprint(bp_transferencias)

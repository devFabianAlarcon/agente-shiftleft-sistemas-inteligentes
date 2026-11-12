"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .movimientos import bp_movimientos
    app.register_blueprint(bp_movimientos)

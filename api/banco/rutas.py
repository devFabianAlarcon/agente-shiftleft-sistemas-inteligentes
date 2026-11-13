"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .preferencias import bp_preferencias
    app.register_blueprint(bp_preferencias)

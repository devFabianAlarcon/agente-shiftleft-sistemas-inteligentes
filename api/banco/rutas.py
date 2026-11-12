"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .registro import bp_registro
    app.register_blueprint(bp_registro)

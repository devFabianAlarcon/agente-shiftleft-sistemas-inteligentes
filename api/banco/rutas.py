"""Registro central de rutas. Cada PR agrega su blueprint aqui."""


def registrar_rutas(app):
    from .sesion import bp_sesion
    app.register_blueprint(bp_sesion)

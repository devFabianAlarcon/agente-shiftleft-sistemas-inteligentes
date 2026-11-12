"""Base de datos SQLite con datos ficticios."""
import hashlib
import secrets
import sqlite3

from flask import current_app, g

ESQUEMA = """
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS cuentas;
DROP TABLE IF EXISTS movimientos;
DROP TABLE IF EXISTS tokens;
DROP TABLE IF EXISTS auditoria;

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    documento TEXT NOT NULL,
    clave_hash TEXT NOT NULL,
    sal TEXT NOT NULL,
    idioma TEXT NOT NULL DEFAULT 'es'
);
CREATE TABLE cuentas (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    numero TEXT UNIQUE NOT NULL,
    saldo REAL NOT NULL,
    limite_diario REAL NOT NULL DEFAULT 2000000
);
CREATE TABLE movimientos (
    id INTEGER PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
    descripcion TEXT NOT NULL,
    valor REAL NOT NULL,
    fecha TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE tokens (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER,
    evento TEXT NOT NULL,
    detalle TEXT,
    fecha TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def hash_clave(clave, sal):
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), 200_000).hex()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    conn.executescript(ESQUEMA)
    # Datos 100 % ficticios
    personas = [("ana", "1000000001", "ClaveAna#2026"), ("beto", "1000000002", "ClaveBeto#2026")]
    for i, (usuario, documento, clave) in enumerate(personas, start=1):
        sal = secrets.token_hex(8)
        conn.execute(
            "INSERT INTO usuarios (id, usuario, documento, clave_hash, sal) VALUES (?, ?, ?, ?, ?)",
            (i, usuario, documento, hash_clave(clave, sal), sal),
        )
        conn.execute(
            "INSERT INTO cuentas (id, usuario_id, numero, saldo, limite_diario) VALUES (?, ?, ?, ?, ?)",
            (i, i, f"0011-{i:04d}", 1_500_000 * i, 500_000),
        )
        conn.execute(
            "INSERT INTO movimientos (cuenta_id, descripcion, valor) VALUES (?, ?, ?)",
            (i, "Pago nomina", 3_000_000),
        )
        # Tokens de prueba para los tests (antes de que exista /login)
        conn.execute("INSERT INTO tokens (token, usuario_id) VALUES (?, ?)", (f"token-prueba-{usuario}", i))
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Base de datos ficticia creada.")

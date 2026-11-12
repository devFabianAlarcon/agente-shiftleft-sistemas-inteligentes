"""Comprueba que cada vulnerabilidad sembrada se puede explotar.

Uso (desde la carpeta api/ con la rama del PR activa):
    python ../evaluacion/verificar_vulnerabilidades.py feature/consulta-saldo
"""
import json, logging, os, sys, tempfile
sys.path.insert(0, os.getcwd())
from banco import create_app
from banco.db import init_db
rama = sys.argv[1]
d = tempfile.mkdtemp()
app = create_app({"TESTING": True, "DATABASE": os.path.join(d, "t.db")})
with app.app_context(): init_db()
c = app.test_client()
ANA = {"Authorization": "Bearer token-prueba-ana"}
r = {}
if rama == "feature/consulta-saldo":
    x = c.get("/cuentas/2/saldo", headers=ANA)  # cuenta de beto
    r["BOLA: ana ve el saldo de beto"] = x.status_code == 200
if rama == "feature/login":
    fallos = [c.post("/login", json={"usuario": "ana", "clave": f"x{i}"}).status_code for i in range(50)]
    ok = c.post("/login", json={"usuario": "ana", "clave": "ClaveAna#2026"}).status_code
    r["Fuerza bruta: 50 intentos fallidos y luego entra"] = all(s == 401 for s in fallos) and ok == 200
    r["Secreto en el codigo"] = "CLAVE_FIRMA = \"" in open("banco/sesion.py").read()
if rama == "feature/transferencias":
    normal = c.post("/transferencias", headers=ANA, json={"cuenta_destino": "0011-0002", "valor": 1_000_000})
    trampa = c.post("/transferencias", headers=ANA, json={"cuenta_destino": "0011-0002", "valor": 1_000_000, "limite_diario": 99_999_999})
    r["Asignacion masiva: limite_diario enviado por el cliente"] = normal.status_code == 400 and trampa.status_code == 200
if rama == "feature/busqueda-movimientos":
    x = c.get("/movimientos?q=%25' OR 1=1 --", headers=ANA)
    r["Inyeccion SQL: ana ve movimientos de beto"] = x.status_code == 200 and len(x.json["movimientos"]) == 2
if rama == "feature/auditoria":
    h = logging.Handler(); msgs = []; h.emit = lambda rec: msgs.append(rec.getMessage())
    logging.getLogger("operaciones").addHandler(h)
    c.post("/health", json={"usuario": "ana", "clave": "ClaveAna#2026", "documento": "1000000001"})
    r["Dato sensible en log"] = any("ClaveAna#2026" in m and "1000000001" in m for m in msgs)
if rama == "feature/idioma":
    x = c.patch("/preferencias/idioma", headers=ANA, json={"idioma": "en'; DROP TABLE usuarios;--"})
    r["Sin falla: rechaza entrada maliciosa"] = x.status_code == 400
print(json.dumps({rama: r}, ensure_ascii=False))

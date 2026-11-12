def test_login_correcto(client):
    r = client.post("/login", json={"usuario": "ana", "clave": "ClaveAna#2026"})
    assert r.status_code == 200
    assert "token" in r.json


def test_login_incorrecto(client):
    r = client.post("/login", json={"usuario": "ana", "clave": "mala"})
    assert r.status_code == 401

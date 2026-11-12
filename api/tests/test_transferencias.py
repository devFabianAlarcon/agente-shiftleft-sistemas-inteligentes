from conftest import ANA


def test_transferencia_valida(client):
    r = client.post("/transferencias", headers=ANA, json={"cuenta_destino": "0011-0002", "valor": 100000})
    assert r.status_code == 200
    assert r.json["estado"] == "aprobada"


def test_transferencia_supera_limite(client):
    r = client.post("/transferencias", headers=ANA, json={"cuenta_destino": "0011-0002", "valor": 1_000_000})
    assert r.status_code == 400

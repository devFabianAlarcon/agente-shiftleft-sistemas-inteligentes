from conftest import ANA


def test_buscar_movimiento(client):
    r = client.get("/movimientos?q=nomina", headers=ANA)
    assert r.status_code == 200
    assert len(r.json["movimientos"]) == 1

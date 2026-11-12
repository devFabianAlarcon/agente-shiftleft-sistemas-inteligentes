from conftest import ANA


def test_consultar_saldo_propio(client):
    r = client.get("/cuentas/1/saldo", headers=ANA)
    assert r.status_code == 200
    assert r.json["saldo"] == 1_500_000

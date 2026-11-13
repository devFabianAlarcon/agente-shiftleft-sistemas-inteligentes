from conftest import ANA


def test_cambiar_idioma(client):
    assert client.patch("/preferencias/idioma", headers=ANA, json={"idioma": "en"}).json["idioma"] == "en"


def test_idioma_invalido(client):
    assert client.patch("/preferencias/idioma", headers=ANA, json={"idioma": "xx"}).status_code == 400

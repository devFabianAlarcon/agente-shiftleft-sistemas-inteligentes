import logging


def test_registra_operacion(client, caplog):
    with caplog.at_level(logging.INFO, logger="operaciones"):
        client.post("/health", json={"x": 1})
    assert any("operacion POST /health" in m for m in caplog.messages)

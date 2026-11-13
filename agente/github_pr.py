"""Lee un pull request del repositorio desde la API pública de GitHub.

Es el equivalente a los nodos "Datos del PR", "Diff del PR" y "Preparar entrada" del flujo
de n8n: entrega al agente la misma entrada (historia de usuario + diff del cambio).

Uso desde la terminal (en la raíz del repositorio):
    python agente/github_pr.py 2
"""
import os
import sys

import requests

REPO = "devFabianAlarcon/agente-shiftleft-sistemas-inteligentes"
URL_PR = f"https://api.github.com/repos/{REPO}/pulls"
MAX_DIFF = 12000  # mismo límite que en n8n, para no exceder el contexto del modelo


def obtener_pr(numero: int) -> dict:
    """Devuelve título, historia de usuario, rama, enlace y diff del PR indicado."""
    cabeceras = {}
    # El repositorio es público, así que el token es opcional. En GitHub Actions se usa
    # para no depender del cupo de peticiones anónimas.
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"

    # 1) Datos del PR en JSON: título, descripción (historia de usuario) y rama.
    datos = requests.get(f"{URL_PR}/{numero}", headers=cabeceras, timeout=30)
    datos.raise_for_status()
    pr = datos.json()

    # 2) El mismo recurso, pedido como diff en texto plano.
    diff = requests.get(
        f"{URL_PR}/{numero}",
        headers={**cabeceras, "Accept": "application/vnd.github.v3.diff"},
        timeout=30,
    )
    diff.raise_for_status()

    return {
        "numero_pr": pr["number"],
        "titulo": pr["title"],
        "historia": pr["body"] or "",
        "rama": pr["head"]["ref"],
        "url_pr": pr["html_url"],
        "diff": diff.text[:MAX_DIFF],
    }


if __name__ == "__main__":
    pr = obtener_pr(int(sys.argv[1]))
    print(f"PR #{pr['numero_pr']}: {pr['titulo']}  ({pr['rama']})")
    print(pr["historia"])
    print(f"--- diff: {len(pr['diff'])} caracteres ---")
    print(pr["diff"][:600])

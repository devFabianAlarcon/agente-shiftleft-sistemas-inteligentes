"""Salidas del agente: matriz de trazabilidad, comentario en el PR y alerta por Telegram.

Equivale a los nodos de n8n "Armar matriz", "Google Sheets", "Armar reporte", "Gmail",
"¿Prioridad alta?" y "Telegram":
- la matriz tiene las mismas 16 columnas y los mismos identificadores (AM-, REQ-, PRU-);
- se guarda en un archivo CSV (en n8n, en Google Sheets);
- el reporte se publica como comentario en el propio PR (en n8n, por Gmail);
- si hay hallazgos de prioridad alta, se avisa por Telegram con el mismo bot.
"""
import csv
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import requests

from github_pr import REPO

COLUMNAS = ["fecha", "ejecucion", "numero_pr", "titulo", "id_amenaza", "stride", "componente",
            "descripcion", "cwe", "control", "id_requisito", "criterio_gherkin", "id_prueba",
            "tipo_prueba", "prioridad", "evidencia"]

MARCA = "<!-- agente-shiftleft -->"   # identifica el comentario del agente para actualizarlo
SIN_ANALISIS = "Sin análisis"         # el modelo no entregó un análisis en ningún intento


def armar_matriz(pr: dict, informe, ejecucion: str) -> list[dict]:
    """Una fila por hallazgo: amenaza -> requisito (Gherkin) -> prueba -> evidencia (el PR)."""
    numero = pr["numero_pr"]
    base = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ejecucion": ejecucion,
        "numero_pr": numero,
        "titulo": pr["titulo"],
        "evidencia": pr["url_pr"],
    }
    vacia = dict.fromkeys(COLUMNAS, "")
    if not informe.analisis_realizado:
        # El modelo se negó o falló: se registra como error, no como "sin amenazas".
        return [{**vacia, **base, "stride": SIN_ANALISIS, "prioridad": "error"}]
    if not informe.hallazgos:
        # PR sin amenazas: se deja una fila para que la corrida quede registrada.
        return [{**vacia, **base, "stride": "Sin hallazgos", "prioridad": "ninguna"}]

    filas = []
    for i, hallazgo in enumerate(informe.hallazgos, start=1):
        digitos = "".join(c for c in hallazgo.cwe if c.isdigit())   # "307" o "CWE-307" -> "CWE-307"
        filas.append({
            **base,
            "id_amenaza": f"AM-PR{numero}-{i}",
            "stride": hallazgo.stride,
            "componente": hallazgo.componente,
            "descripcion": hallazgo.descripcion,
            "cwe": f"CWE-{digitos}" if digitos else "",
            "control": hallazgo.control,
            "id_requisito": f"REQ-PR{numero}-{i}",
            "criterio_gherkin": hallazgo.criterio_gherkin,
            "id_prueba": f"PRU-PR{numero}-{i}",
            "tipo_prueba": hallazgo.tipo_prueba,
            "prioridad": hallazgo.prioridad,
        })
    return filas


def guardar_csv(filas: list[dict], ruta: Path) -> None:
    """Agrega las filas al final del CSV; si el archivo no existe, lo crea con encabezados."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not ruta.exists()
    with ruta.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        if nuevo:
            escritor.writeheader()
        escritor.writerows(filas)


def _reales(filas: list[dict]) -> list[dict]:
    """Descarta la fila 'Sin hallazgos'."""
    return [f for f in filas if f["id_amenaza"]]


def _celda(texto) -> str:
    """Deja un texto apto para una celda de tabla Markdown."""
    return str(texto).replace("|", "\\|").replace("\n", "<br>")


def armar_comentario(pr: dict, filas: list[dict], segundos: float) -> str:
    """Reporte en Markdown para publicar en el PR."""
    reales = _reales(filas)
    lineas = [MARCA, f"## 🔐 Revisión de seguridad del PR #{pr['numero_pr']} (agente LangChain)", ""]
    if filas[0]["stride"] == SIN_ANALISIS:
        lineas.append("⚠️ El agente no pudo completar el análisis (el modelo se negó a responder o "
                      "falló). Este cambio **no fue revisado**: hay que relanzar la revisión.")
    elif not reales:
        lineas.append("El agente no encontró amenazas en este cambio.")
    else:
        altas = sum(f["prioridad"] == "alta" for f in reales)
        lineas += [f"**{len(reales)} hallazgo(s)**, {altas} de prioridad alta.", "",
                   "| Amenaza | STRIDE | CWE | Descripción | Control | Requisito (Gherkin) | Prueba | Prioridad |",
                   "|---|---|---|---|---|---|---|---|"]
        for f in reales:
            lineas.append(
                f"| {f['id_amenaza']} | {_celda(f['stride'])} | {f['cwe']} | {_celda(f['descripcion'])} "
                f"| {_celda(f['control'])} | **{f['id_requisito']}**<br>{_celda(f['criterio_gherkin'])} "
                f"| **{f['id_prueba']}**<br>{f['tipo_prueba']} | {f['prioridad']} |")
    lineas += ["", f"<sub>Análisis automático en {segundos} s · ejecución {filas[0]['ejecucion']}</sub>"]
    return "\n".join(lineas)


def comentar_pr(numero: int, texto: str) -> str:
    """Publica el reporte en el PR. Si el agente ya había comentado, actualiza ese comentario."""
    cabeceras = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json"}
    api = f"https://api.github.com/repos/{REPO}/issues"

    comentarios = requests.get(f"{api}/{numero}/comments", headers=cabeceras,
                               params={"per_page": 100}, timeout=30)
    comentarios.raise_for_status()
    anterior = next((c for c in comentarios.json() if MARCA in c["body"]), None)

    if anterior:
        respuesta = requests.patch(f"{api}/comments/{anterior['id']}", headers=cabeceras,
                                   json={"body": texto}, timeout=30)
    else:
        respuesta = requests.post(f"{api}/{numero}/comments", headers=cabeceras,
                                  json={"body": texto}, timeout=30)
    respuesta.raise_for_status()
    return respuesta.json()["html_url"]


def avisar_telegram(pr: dict, filas: list[dict]) -> bool:
    """Envía la alerta solo si hay hallazgos de prioridad alta. Devuelve True si la envió."""
    altas = [f for f in _reales(filas) if f["prioridad"] == "alta"]
    if not altas:
        return False
    texto = (f"🚨 <b>PR #{pr['numero_pr']}: {escape(pr['titulo'])}</b> (agente LangChain)\n"
             f"{len(altas)} hallazgo(s) de prioridad alta:\n"
             + "\n".join(f"• {f['id_amenaza']} — {escape(f['stride'])} ({f['cwe'] or 'sin CWE'})"
                         for f in altas)
             + f"\n{pr['url_pr']}")
    respuesta = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": texto, "parse_mode": "HTML"},
        timeout=30)
    respuesta.raise_for_status()
    return True

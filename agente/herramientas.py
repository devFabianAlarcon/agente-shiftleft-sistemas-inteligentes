"""Herramientas (tools) que el agente puede usar mientras razona.

Son las mismas dos del flujo de n8n, con los mismos nombres:
- buscar_owasp   -> nodo "Supabase Vector Store" usado como herramienta.
- consultar_cwe  -> nodo "HTTP Request Tool" contra el catálogo CWE de MITRE.

El texto entre comillas triples de cada función es la descripción que lee el modelo
para decidir cuándo usarla.

Prueba rápida desde la terminal (en la raíz del repositorio):
    python agente/herramientas.py
"""
import requests
from langchain_core.tools import tool

from base_conocimiento import cargar_indice

URL_CWE = "https://cwe-api.mitre.org/api/v1/cwe/weakness"
K_FRAGMENTOS = 4   # igual que el límite del nodo de n8n

_indice = None     # el índice se carga una sola vez, la primera vez que se necesita


@tool
def buscar_owasp(consulta: str) -> str:
    """Busca fragmentos de OWASP ASVS, OWASP API Security Top 10 y Threat Modeling
    Cheat Sheet. Úsala para encontrar el control de seguridad que mitiga una amenaza.
    Entrada: descripción breve de la amenaza en inglés."""
    global _indice
    if _indice is None:
        _indice = cargar_indice()
    fragmentos = _indice.similarity_search(consulta, k=K_FRAGMENTOS)
    return "\n\n".join(f"[{f.metadata['fuente']}]\n{f.page_content}" for f in fragmentos)


@tool
def consultar_cwe(numero: str) -> str:
    """Consulta una debilidad en el catálogo CWE de MITRE para confirmar que existe.
    Entrada: solo el número del CWE, por ejemplo 89."""
    numero = "".join(c for c in str(numero) if c.isdigit())   # acepta "CWE-89" o "89"
    if not numero:
        return "Entrada inválida: se espera el número del CWE."
    try:
        respuesta = requests.get(f"{URL_CWE}/{numero}", timeout=30)
    except requests.RequestException as error:
        return f"No se pudo consultar MITRE: {error}"
    if respuesta.status_code == 404:
        return f"CWE-{numero} no existe en el catálogo de MITRE."
    if respuesta.status_code != 200:
        return f"MITRE respondió {respuesta.status_code} para CWE-{numero}."
    # De toda la ficha solo se devuelven tres campos, igual que en n8n (Optimize Response).
    debilidad = respuesta.json()["Weaknesses"][0]
    return f"CWE-{debilidad['ID']}: {debilidad['Name']}. {debilidad['Description']}"


HERRAMIENTAS = [buscar_owasp, consultar_cwe]


if __name__ == "__main__":
    print(consultar_cwe.invoke("307"))
    print(consultar_cwe.invoke("99999"))
    print("---")
    print(buscar_owasp.invoke("brute force login rate limiting")[:700])

"""Base de conocimiento del agente (RAG): documentos OWASP en un índice FAISS local.

Es el equivalente al flujo auxiliar de n8n "Carga de fuentes OWASP": descarga las mismas
9 fuentes públicas, las parte en fragmentos, calcula sus embeddings y las guarda en un
almacén de vectores. Aquí el almacén es FAISS en disco (en n8n es Supabase).

Uso desde la terminal (en la raíz del repositorio), una sola vez:
    python agente/base_conocimiento.py

Requiere la variable de entorno GOOGLE_API_KEY (clave de Google AI Studio).
"""
import time
import warnings
from pathlib import Path

import requests
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

warnings.filterwarnings("ignore")  # silencia el aviso de retiro de langchain-community
from langchain_community.vectorstores import FAISS  # noqa: E402

RUTA_INDICE = Path(__file__).parent / "indice_faiss"   # carpeta ignorada por git
MODELO_EMBEDDINGS = "models/gemini-embedding-001"
TAMANO_LOTE = 50        # fragmentos por petición de embeddings
PAUSA_ENTRE_LOTES = 20  # segundos; evita el tope por minuto de la capa gratuita

_ASVS = "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/"
_API = "https://raw.githubusercontent.com/OWASP/API-Security/master/editions/2023/en/"

FUENTES = [
    ("Threat Modeling Cheat Sheet",
     "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Threat_Modeling_Cheat_Sheet.md"),
    ("API Top 10 - API1 BOLA", _API + "0xa1-broken-object-level-authorization.md"),
    ("API Top 10 - API2 Autenticacion", _API + "0xa2-broken-authentication.md"),
    ("API Top 10 - API3 Propiedades", _API + "0xa3-broken-object-property-level-authorization.md"),
    ("ASVS V2 Autenticacion", _ASVS + "0x11-V2-Authentication.md"),
    ("ASVS V4 Control de acceso", _ASVS + "0x12-V4-Access-Control.md"),
    ("ASVS V5 Validacion", _ASVS + "0x13-V5-Validation-Sanitization-Encoding.md"),
    ("ASVS V6 Criptografia", _ASVS + "0x14-V6-Cryptography.md"),
    ("ASVS V7 Errores y logs", _ASVS + "0x15-V7-Error-Logging.md"),
]


def crear_embeddings():
    """Modelo de embeddings de Google; lee la clave de GOOGLE_API_KEY."""
    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)


def descargar_fragmentos() -> list[Document]:
    """Descarga las fuentes y las parte en fragmentos de 500 caracteres con solape de 100."""
    documentos = []
    for fuente, url in FUENTES:
        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()
        documentos.append(Document(page_content=respuesta.text, metadata={"fuente": fuente}))

    separador = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return separador.split_documents(documentos)


def construir_indice(embeddings=None) -> FAISS:
    """Crea el índice FAISS desde cero y lo guarda en disco."""
    embeddings = embeddings or crear_embeddings()
    fragmentos = descargar_fragmentos()
    print(f"{len(FUENTES)} fuentes -> {len(fragmentos)} fragmentos")

    indice = None
    for inicio in range(0, len(fragmentos), TAMANO_LOTE):
        lote = fragmentos[inicio:inicio + TAMANO_LOTE]
        if indice is None:
            indice = FAISS.from_documents(lote, embeddings)
        else:
            time.sleep(PAUSA_ENTRE_LOTES)
            indice.add_documents(lote)
        print(f"  indexados {min(inicio + TAMANO_LOTE, len(fragmentos))}/{len(fragmentos)}")

    indice.save_local(str(RUTA_INDICE))
    return indice


def cargar_indice(embeddings=None) -> FAISS:
    """Carga el índice guardado; si todavía no existe, lo construye."""
    embeddings = embeddings or crear_embeddings()
    if not RUTA_INDICE.exists():
        return construir_indice(embeddings)
    # El índice lo genera este mismo proyecto, por eso es seguro deserializarlo.
    return FAISS.load_local(str(RUTA_INDICE), embeddings, allow_dangerous_deserialization=True)


if __name__ == "__main__":
    construir_indice()
    print(f"Índice guardado en {RUTA_INDICE}")

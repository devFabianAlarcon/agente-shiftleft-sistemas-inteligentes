"""Agente de revisión de seguridad de un pull request (Nivel 2, LangChain).

Mismo caso que el flujo de n8n: recibe la historia de usuario y el diff de un PR, modela
las amenazas con STRIDE y devuelve hallazgos con CWE, control, criterio Gherkin y prueba.

Componentes:
- LLM:      Gemini (ChatGoogleGenerativeAI), temperatura 0.
- Prompt:   ChatPromptTemplate con mensaje de sistema y plantilla humana con variables.
- Tools:    buscar_owasp (RAG sobre FAISS) y consultar_cwe (catálogo de MITRE).
- Agente:   ReAct de LangGraph (create_react_agent): el modelo razona, decide qué
            herramienta usar, observa el resultado y repite hasta poder responder.
- Salida:   una cadena LCEL (prompt | modelo con salida estructurada) convierte la
            respuesta final del agente en un objeto Informe validado con Pydantic.

Uso desde la terminal (en la raíz del repositorio), con GOOGLE_API_KEY definida:
    python agente/agente.py 2
"""
import sys
import time
import warnings
from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore")  # avisos de retiro de LangGraph, como en clase
from langgraph.prebuilt import create_react_agent  # noqa: E402

from github_pr import obtener_pr  # noqa: E402
from herramientas import HERRAMIENTAS  # noqa: E402

MODELO = "gemini-3.5-flash"   # el mismo modelo del flujo de n8n
TEMPERATURA = 0               # 0 = respuestas lo más repetibles posible
INCLUIR_PENSAMIENTOS = True   # pide a Gemini el resumen de su razonamiento para la traza
MAX_INTENTOS = 3              # reintentos si el modelo se niega o no entrega un análisis

# ---------------------------------------------------------------------------
# 1. Prompt. El mensaje de sistema es el mismo texto del AI Agent de n8n,
#    para que los dos niveles se comparen con las mismas instrucciones.
# ---------------------------------------------------------------------------
SISTEMA = """Eres un analista de seguridad de aplicaciones (AppSec) que revisa pull requests de una API bancaria.

Tu tarea:
1. Modela las amenazas del cambio con STRIDE. Analiza SOLO las líneas que el diff agrega o modifica, no el resto del sistema.
2. Para cada amenaza real, escribe un criterio de aceptación de seguridad verificable en formato Gherkin (Dado / Cuando / Entonces), en español.
3. Propón el tipo de prueba que lo valida: SAST, DAST o unitaria.

Reglas:
- Usa la herramienta buscar_owasp para sustentar el control que propones.
- Usa la herramienta consultar_cwe para confirmar que el identificador CWE existe y corresponde. No inventes identificadores: si no puedes confirmarlo, deja el campo cwe vacío.
- stride debe ser una de: Suplantación, Manipulación, Repudio, Divulgación de información, Denegación de servicio, Elevación de privilegios.
- prioridad debe ser: alta, media o baja.
- Si el cambio no introduce amenazas, devuelve la lista hallazgos vacía. No reportes hallazgos para rellenar.
- Cuando ya tengas la información necesaria, entrega la respuesta final en el formato pedido. Nunca escribas una llamada a herramienta como texto.
"""

# En n8n el Structured Output Parser agrega por su cuenta la lista de campos al mensaje de
# sistema. Aquí se escribe a mano para que la respuesta final del agente ya los traiga.
CAMPOS = """
En la respuesta final, cada hallazgo debe traer exactamente estos campos: stride, componente (archivo y
función o endpoint), descripcion, cwe, control (incluye la referencia OWASP que lo sustenta),
criterio_gherkin, tipo_prueba y prioridad.
"""

HUMANO = """Pull request #{numero_pr}: {titulo}

Historia de usuario:
{historia}

Cambio de código (diff):
{diff}"""

PROMPT = ChatPromptTemplate.from_messages([("system", SISTEMA + CAMPOS), ("human", HUMANO)])


# ---------------------------------------------------------------------------
# 2. Salida estructurada. Los mismos 8 campos del Structured Output Parser de n8n.
#    Pydantic rechaza cualquier valor que no esté en las listas permitidas.
# ---------------------------------------------------------------------------
class Hallazgo(BaseModel):
    stride: Literal["Suplantación", "Manipulación", "Repudio", "Divulgación de información",
                    "Denegación de servicio", "Elevación de privilegios"]
    componente: str = Field(description="Archivo y función o endpoint afectado")
    descripcion: str = Field(description="Descripción breve de la amenaza")
    cwe: str = Field(description="Identificador confirmado, por ejemplo CWE-307; vacío si no se confirmó")
    control: str = Field(description="Control de seguridad que mitiga la amenaza")
    criterio_gherkin: str = Field(description="Criterio de aceptación: Dado / Cuando / Entonces")
    tipo_prueba: Literal["SAST", "DAST", "unitaria"]
    prioridad: Literal["alta", "media", "baja"]


class Informe(BaseModel):
    analisis_realizado: bool = Field(
        description="true si el texto contiene un análisis de seguridad del cambio (con o sin amenazas); "
                    "false si es una negativa a responder, un error o no analiza el cambio")
    hallazgos: list[Hallazgo] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. Agente ReAct y cadena de formato.
# ---------------------------------------------------------------------------
# Segundo prompt: solo da formato. Va en una llamada aparte porque Gemini no acepta
# que la conversación del agente termine en un turno del modelo para pedirle el JSON.
PROMPT_FORMATO = ChatPromptTemplate.from_messages([
    ("system",
     "Convierte el análisis de seguridad en el formato estructurado pedido. "
     "No agregues, quites ni cambies hallazgos: solo ubica cada dato en su campo. "
     "Escribe cwe como CWE-número (por ejemplo CWE-307) o déjalo vacío si el análisis no lo confirma. "
     "Si el análisis dice que no hay amenazas, devuelve la lista hallazgos vacía. "
     "Si el texto no es un análisis (por ejemplo, el modelo se negó a responder), "
     "marca analisis_realizado como false."),
    ("human", "{analisis}"),
])


def crear_llm():
    """Modelo de lenguaje; lee la clave de la variable de entorno GOOGLE_API_KEY."""
    return ChatGoogleGenerativeAI(model=MODELO, temperature=TEMPERATURA,
                                  include_thoughts=INCLUIR_PENSAMIENTOS)


def crear_agente(llm):
    """Agente ReAct: el modelo decide en cada paso si usa una herramienta o responde."""
    return create_react_agent(model=llm, tools=HERRAMIENTAS)


def _texto(mensaje) -> str:
    """Texto de un mensaje (Gemini a veces lo entrega partido en bloques)."""
    return str(mensaje.text).strip()


def _pensamiento(mensaje) -> str:
    """Resumen del razonamiento del modelo, si el mensaje lo trae."""
    if not isinstance(mensaje.content, list):
        return ""
    partes = [bloque.get("thinking") or bloque.get("reasoning") or ""
              for bloque in mensaje.content
              if isinstance(bloque, dict) and bloque.get("type") in ("thinking", "reasoning")]
    return " ".join(p.strip() for p in partes if isinstance(p, str) and p.strip())


def analizar_pr(numero: int, llm=None, mostrar_traza: bool = True) -> dict:
    """Analiza un PR y devuelve el informe, la traza de razonamiento y el tiempo."""
    llm = llm or crear_llm()
    agente = crear_agente(llm)
    pr = obtener_pr(numero)
    mensajes = PROMPT.invoke(pr).to_messages()   # rellena {numero_pr}, {titulo}, {historia}, {diff}

    traza = []          # pasos del ciclo Pensamiento -> Acción -> Observación

    def registrar(tipo: str, texto: str):
        traza.append((tipo, texto))
        if mostrar_traza:
            print(f"[{tipo}] {texto}\n")

    dar_formato = PROMPT_FORMATO | llm.with_structured_output(Informe)
    informe = Informe(analisis_realizado=False)
    inicio = time.time()

    for intento in range(1, MAX_INTENTOS + 1):
        analisis = ""               # respuesta final del agente, en texto libre
        vistos = len(mensajes)      # mensajes ya procesados (al inicio, los del prompt)

        # Paso 1: el agente razona. stream_mode="values" entrega el estado completo después
        # de cada paso; de cada entrega solo se miran los mensajes nuevos.
        for estado in agente.stream({"messages": mensajes}, stream_mode="values"):
            for mensaje in estado["messages"][vistos:]:
                if isinstance(mensaje, AIMessage) and (_pensamiento(mensaje) or
                                                       (mensaje.tool_calls and _texto(mensaje))):
                    registrar("Pensamiento", _pensamiento(mensaje) or _texto(mensaje))
                if isinstance(mensaje, AIMessage) and mensaje.tool_calls:
                    for llamada in mensaje.tool_calls:
                        registrar("Acción", f"{llamada['name']}({llamada['args']})")
                elif isinstance(mensaje, AIMessage):      # sin herramientas: ya terminó
                    analisis = _texto(mensaje)
                    registrar("Respuesta final", analisis)
                elif isinstance(mensaje, ToolMessage):
                    registrar("Observación", _texto(mensaje)[:300])
            vistos = len(estado["messages"])

        # Paso 2: cadena LCEL que pasa la respuesta final al formato Informe.
        if analisis:
            informe = dar_formato.invoke({"analisis": analisis})

        # Una negativa del modelo NO es lo mismo que "sin amenazas": se reintenta.
        if informe.analisis_realizado:
            break
        informe = Informe(analisis_realizado=False)
        registrar("Reintento", f"intento {intento} de {MAX_INTENTOS}: el modelo no entregó un análisis")

    return {
        "pr": pr,
        "informe": informe,          # objeto Informe ya validado por Pydantic
        "traza": traza,
        "intentos": intento,
        "segundos": round(time.time() - inicio, 1),
    }


if __name__ == "__main__":
    resultado = analizar_pr(int(sys.argv[1]))
    print("=" * 70)
    print(f"PR #{resultado['pr']['numero_pr']}: {len(resultado['informe'].hallazgos)} hallazgo(s) "
          f"en {resultado['segundos']} s")
    print(resultado["informe"].model_dump_json(indent=2))

# Banco Unal Manizales (ficticio) — API de prueba

API pequeña en Flask creada **solo** para el proyecto final de la asignatura *Sistemas Inteligentes*
(UNAL Manizales). Sirve como caso de prueba para un agente de IA que revisa la seguridad de cada
cambio de código (pull request): modela amenazas con STRIDE, propone criterios de aceptación de
seguridad verificables y la prueba que valida cada uno.

> ⚠️ **El banco y todos sus datos son ficticios.** Varias ramas `feature/*` introducen
> vulnerabilidades **a propósito** para medir al agente. No usar este código en producción.

## Cómo correrla

```bash
cd api
pip install -r requirements.txt
flask --app banco init-db
flask --app banco run
pytest
```

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `api/` | API del banco ficticio (Flask). Los 6 PR solo modifican esta carpeta |
| `n8n/` | Flujos exportados de n8n (Nivel 1) |
| `agente/` | Notebook y código del agente en LangChain (Nivel 2) |
| `sistema_experto/` | Reglas y motor de inferencia (Nivel 3) |
| `evaluacion/` | Verdad de referencia, verificación de vulnerabilidades y resultados |

## Cambios de prueba (un pull request por rama)

| PR | Rama | Historia de usuario |
|---|---|---|
| 1 | `feature/consulta-saldo` | Consultar el saldo de una cuenta |
| 2 | `feature/login` | Iniciar sesión con usuario y contraseña |
| 3 | `feature/transferencias` | Transferir dinero entre cuentas |
| 4 | `feature/busqueda-movimientos` | Buscar movimientos por texto |
| 5 | `feature/auditoria` | Registrar las operaciones para auditoría |
| 6 | `feature/idioma` | Cambiar el idioma de la interfaz |

La lista de vulnerabilidades sembradas (verdad de referencia) está en
`evaluacion/verdad_referencia.json`. El agente solo lee el diff y la descripción de cada PR,
así que este archivo no le da pistas.

## Uso de IA generativa

Este proyecto es de autoría del estudiante. Se usó IA generativa (Claude, de Anthropic) únicamente
como herramienta de apoyo, en estas tareas:

- Borradores iniciales del código de la API de prueba y de sus pruebas con pytest.
- Redacción y corrección de estilo de la documentación.

La definición del caso, las vulnerabilidades sembradas, las decisiones de diseño y los resultados
son responsabilidad del autor, que revisó, adaptó y verificó todo el código entregado
(ver `evaluacion/verificar_vulnerabilidades.py`).

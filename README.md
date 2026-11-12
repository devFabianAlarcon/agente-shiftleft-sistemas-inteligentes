# Banco Andino Digital (ficticio) — API de prueba

API pequeña en Flask creada **solo** para el proyecto final de la asignatura *Sistemas Inteligentes*
(UNAL Manizales). Sirve como caso de prueba para un agente de IA que revisa la seguridad de cada
cambio de código (pull request): modela amenazas con STRIDE, propone criterios de aceptación de
seguridad verificables y la prueba que valida cada uno.

> ⚠️ **El banco y todos sus datos son ficticios.** Varias ramas `feature/*` introducen
> vulnerabilidades **a propósito** para medir al agente. No usar este código en producción.

## Cómo correrla

```bash
pip install -r requirements.txt
flask --app banco init-db
flask --app banco run
pytest
```

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
`evaluacion/verdad_referencia.json`, solo en la rama `evaluacion` para no "contaminar" lo que
lee el agente.

## Uso de IA generativa

El código de esta API fue generado con apoyo de Claude (Anthropic) y revisado por el autor.
(Completar con el detalle de qué partes y cómo se adaptaron.)

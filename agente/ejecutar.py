"""Punto de entrada: analiza un PR y entrega las salidas. Es lo que corre el pipeline.

Uso (en la raíz del repositorio, con GOOGLE_API_KEY definida):
    python agente/ejecutar.py 2
    python agente/ejecutar.py 2 --comentar --telegram

--comentar  publica el reporte en el PR (requiere GITHUB_TOKEN con permiso de escritura).
--telegram  avisa si hay prioridad alta (requiere TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID).
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from agente import analizar_pr
from salidas import armar_comentario, armar_matriz, avisar_telegram, comentar_pr, guardar_csv

RUTA_CSV = Path(__file__).parent.parent / "evaluacion" / "resultados" / "matriz_langchain.csv"


def main():
    opciones = argparse.ArgumentParser(description="Revisión de seguridad de un pull request")
    opciones.add_argument("pr", type=int, help="número del pull request")
    opciones.add_argument("--comentar", action="store_true", help="publicar el reporte en el PR")
    opciones.add_argument("--telegram", action="store_true", help="avisar por Telegram si hay prioridad alta")
    args = opciones.parse_args()

    resultado = analizar_pr(args.pr)
    pr = resultado["pr"]

    # En GitHub Actions se usa el número de la corrida; en local, la fecha y hora.
    ejecucion = os.environ.get("GITHUB_RUN_ID") or datetime.now().strftime("local-%Y%m%d-%H%M%S")
    filas = armar_matriz(pr, resultado["informe"], ejecucion)

    guardar_csv(filas, RUTA_CSV)
    print("=" * 70)
    analizado = resultado["informe"].analisis_realizado
    print(f"PR #{pr['numero_pr']}: "
          + (f"{len(resultado['informe'].hallazgos)} hallazgo(s)" if analizado else "SIN ANÁLISIS")
          + f" en {resultado['segundos']} s ({resultado['intentos']} intento(s))")
    print(f"Matriz guardada en {RUTA_CSV}")

    comentario = armar_comentario(pr, filas, resultado["segundos"])
    if args.comentar:
        print("Comentario publicado:", comentar_pr(pr["numero_pr"], comentario))
    else:
        print(comentario)

    if args.telegram:
        print("Alerta por Telegram:", "enviada" if avisar_telegram(pr, filas) else "no aplica (sin prioridad alta)")

    # Si no hubo análisis, el pipeline debe quedar en rojo: el PR no fue revisado.
    if not analizado:
        sys.exit(1)


if __name__ == "__main__":
    main()

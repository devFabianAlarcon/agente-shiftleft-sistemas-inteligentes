#!/usr/bin/env bash
# Publica el repositorio y abre los 6 pull requests en GitHub.
# Requisitos: GitHub CLI (gh) con sesion iniciada: gh auth login
# Uso: ./publicar_en_github.sh TU_USUARIO/NOMBRE_DEL_REPO
set -euo pipefail
REPO="$1"
git remote add origin "https://github.com/$REPO.git" 2>/dev/null || git remote set-url origin "https://github.com/$REPO.git"
git push -u origin main
pr() { # rama, titulo, historia
  git push -u origin "$1"
  gh pr create --repo "$REPO" --base main --head "$1" --title "$2" --body "$3"
}
pr feature/consulta-saldo      "Consulta de saldo por cuenta" \
   "**Historia de usuario:** Como cliente quiero consultar el saldo de mi cuenta para saber cuánto dinero tengo."
pr feature/login               "Inicio de sesión" \
   "**Historia de usuario:** Como cliente quiero iniciar sesión con usuario y contraseña para usar la banca en línea."
pr feature/transferencias      "Transferencias entre cuentas" \
   "**Historia de usuario:** Como cliente quiero transferir dinero desde mi cuenta a otra cuenta del banco, respetando mi límite diario."
pr feature/busqueda-movimientos "Búsqueda de movimientos" \
   "**Historia de usuario:** Como cliente quiero buscar mis movimientos por una palabra de la descripción para encontrar un pago específico."
pr feature/auditoria           "Registro de operaciones para auditoría" \
   "**Historia de usuario:** Como oficial de cumplimiento quiero que quede registro de cada operación recibida por la API para poder auditarla después."
pr feature/idioma              "Cambio de idioma" \
   "**Historia de usuario:** Como cliente quiero cambiar el idioma de la interfaz entre español e inglés."
echo "Listo: https://github.com/$REPO/pulls"

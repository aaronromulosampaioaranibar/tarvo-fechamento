#!/bin/bash
cd "$(dirname "$0")"
echo
echo "  ============================================"
echo "    FECHAMENTO TARVO"
echo "  ============================================"
echo
echo "  Deixe esta janela aberta enquanto usa a tela."
echo
if ! command -v python3 >/dev/null 2>&1; then
  echo "  Python 3 nao encontrado. Instale em https://python.org/downloads"
  echo; read -p "  Aperte Enter para fechar." _; exit 1
fi
python3 -m pip install --quiet --disable-pip-version-check openpyxl 2>/dev/null
python3 abrir.py
echo
echo "  O fechamento foi encerrado."
read -p "  Aperte Enter para fechar." _

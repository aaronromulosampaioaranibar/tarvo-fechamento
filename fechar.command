#!/bin/bash
cd "$(dirname "$0")"
echo
echo "  ============================================"
echo "    FECHAMENTO DO MES - TARVO PAGAMENTOS"
echo "  ============================================"
echo
python3 fechar.py
ok=$?
echo
if [ $ok -eq 0 ]; then
  echo "  PRONTO. Os arquivos estao na pasta saida."
  (open saida 2>/dev/null || xdg-open saida 2>/dev/null) &
else
  echo "  NAO FECHOU. Nada foi gravado - o motivo esta acima."
fi
echo
read -n 1 -s -r -p "  Pode fechar esta janela."

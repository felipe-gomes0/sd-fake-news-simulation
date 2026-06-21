#!/usr/bin/env bash
# Regenera benchmark, graficos e PDF na maquina de teste do grupo.
set -e
cd "$(dirname "$0")/codigo"
echo ">> Validando corretude..."
python3 analise/testar_corretude.py
echo ">> Rodando benchmark (use --completo para varredura maior)..."
python3 analise/benchmark.py "$@"
echo ">> Gerando graficos..."
python3 analise/gerar_graficos.py
echo ">> Gerando apresentacao PDF..."
python3 analise/gerar_apresentacao.py
echo ">> Pronto. Veja resultados/, graficos/ e Apresentacao_FakeNews.pdf"

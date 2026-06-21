"""
FakeNews_worker.py
==================
Processo WORKER da versao distribuida.

Conecta-se ao servidor (master) e, a cada geracao, recebe um BLOCO da matriz
contendo suas linhas reais MAIS as linhas-fantasma (ghost rows) necessarias
para calcular a vizinhanca de Moore nas fronteiras. Calcula a proxima geracao
apenas das LINHAS REAIS e devolve o resultado ao master.

Por que ghost rows?
  Para decidir o proximo estado de uma celula na PRIMEIRA ou ULTIMA linha do
  seu pedaco, o worker precisa "enxergar" uma linha do pedaco vizinho. Essas
  linhas emprestadas (so leitura) sao as ghost rows. Sem elas, as fronteiras
  ficariam inconsistentes em relacao a versao sequencial.

O worker e "burro" de proposito: nao guarda estado entre geracoes. Toda a
coordenacao (montar blocos, juntar resultados) e responsabilidade do master.
Isso reduz acoplamento e facilita rodar workers em maquinas diferentes.

Uso:
    python FakeNews_worker.py --host 127.0.0.1 --porta 9099
"""

import argparse
import socket

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

from nucleo import proxima_celula
from protocolo import enviar_msg, receber_msg


def processar_bloco(bloco, ini_real, fim_real, limiar):
    """
    Calcula a proxima geracao das linhas [ini_real, fim_real) do 'bloco',
    usando o bloco inteiro (incluindo ghost rows) como contexto de vizinhanca.
    Retorna apenas as linhas reais ja atualizadas.
    """
    colunas = len(bloco[0])
    resultado = []
    for i in range(ini_real, fim_real):
        nova_linha = [proxima_celula(bloco, i, j, limiar) for j in range(colunas)]
        resultado.append(nova_linha)
    return resultado


def main():
    p = argparse.ArgumentParser(description="Worker distribuido de fake news")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=9099)
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.porta))
    print(f"[WORKER {sock.getsockname()}] conectado ao master {args.host}:{args.porta}")

    geracoes_processadas = 0
    while True:
        msg = receber_msg(sock)
        if msg is None or msg.get("tipo") == "fim":
            break
        # msg: {tipo:"processar", bloco:[...], ini_real:x, fim_real:y, limiar:k}
        resultado = processar_bloco(
            msg["bloco"], msg["ini_real"], msg["fim_real"], msg["limiar"]
        )
        enviar_msg(sock, {"linhas": resultado})
        geracoes_processadas += 1

    print(f"[WORKER] encerrando. Geracoes processadas: {geracoes_processadas}")
    sock.close()


if __name__ == "__main__":
    main()

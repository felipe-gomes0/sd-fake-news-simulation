"""
FakeNews_servidor.py
====================
Processo MASTER (servidor) da versao DISTRIBUIDA com SOCKETS.

Arquitetura Master-Worker:
  - O master mantem a matriz global e divide as LINHAS em faixas contiguas
    (uma faixa por worker) -> divisao explicita do trabalho.
  - A cada geracao, para cada worker, o master monta um BLOCO contendo:
        [ghost row de cima?] + linhas reais do worker + [ghost row de baixo?]
    As ghost rows sao copias das linhas vizinhas (sincronizacao de fronteira).
  - Os blocos sao enviados a TODOS os workers (em paralelo, via threads de
    I/O so para sobrepor a comunicacao), os resultados sao recebidos e o
    master remonta a nova matriz global -> consistencia de geracao garantida.

Observacao sobre as threads do master: elas servem apenas para SOBREPOR a
ESPERA de rede (I/O-bound), nao para calcular a simulacao. O calculo de CPU
acontece nos PROCESSOS worker, que sao independentes e nao sofrem com o GIL
do master.

Uso (em terminais separados):
    # 1) suba os workers
    python FakeNews_worker.py --porta 9099
    python FakeNews_worker.py --porta 9099
    # 2) suba o master apontando o numero de workers
    python FakeNews_servidor.py --workers 2 --porta 9099
"""

import time
import argparse
import socket
import threading

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

from nucleo import (
    IGNORANTE, ESPALHADOR, INATIVO,
    criar_grade, contar_estados, calcular_faixas,
)
from protocolo import enviar_msg, receber_msg


def montar_bloco(grade, ini, fim):
    """
    Monta o bloco do worker que cobre as linhas [ini, fim):
      - inclui a linha ini-1 como ghost (se existir)
      - inclui a linha fim como ghost (se existir)
    Retorna (bloco, ini_real, fim_real) onde [ini_real, fim_real) sao os
    indices DENTRO do bloco que correspondem as linhas reais do worker.
    """
    linhas = len(grade)
    topo = ini - 1 if ini > 0 else ini          # primeira linha a copiar
    base = fim + 1 if fim < linhas else fim      # limite (exclusivo) a copiar
    bloco = [grade[k][:] for k in range(topo, base)]
    ini_real = ini - topo          # 0 se nao ha ghost no topo, senao 1
    fim_real = ini_real + (fim - ini)
    return bloco, ini_real, fim_real


def comunicar_worker(idx, conexao, grade, faixa, limiar, resultados, erros):
    """Envia o bloco ao worker idx e guarda a resposta em resultados[idx]."""
    try:
        ini, fim = faixa
        bloco, ini_real, fim_real = montar_bloco(grade, ini, fim)
        enviar_msg(conexao, {
            "tipo": "processar",
            "bloco": bloco,
            "ini_real": ini_real,
            "fim_real": fim_real,
            "limiar": limiar,
        })
        resposta = receber_msg(conexao)
        if resposta is None:
            erros[idx] = "conexao fechada"
        else:
            resultados[idx] = resposta["linhas"]
    except Exception as e:  # noqa
        erros[idx] = str(e)


def executar_simulacao(linhas=100, colunas=100, geracoes=50,
                       percentual_espalhadores=0.05, limiar_convencimento=3,
                       num_workers=2, host="127.0.0.1", porta=9099, verbose=True):
    # --- aceita as conexoes dos workers ---
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((host, porta))
    servidor.listen(num_workers)
    if verbose:
        print(f"[MASTER] aguardando {num_workers} worker(s) na porta {porta}...")

    conexoes = []
    for i in range(num_workers):
        conn, addr = servidor.accept()
        conexoes.append(conn)
        if verbose:
            print(f"[MASTER] worker {i} conectado: {addr}")

    grade = criar_grade(linhas, colunas, percentual_espalhadores)
    faixas = calcular_faixas(linhas, num_workers)

    if verbose:
        print("\n=== SIMULACAO DISTRIBUIDA (SOCKETS) DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Grade: {linhas} x {colunas} ({linhas*colunas:,} pessoas) | "
              f"Geracoes: {geracoes} | Workers: {num_workers} | Limiar: {limiar_convencimento}")
        print(f"Faixas por worker: {faixas}\n")

    inicio = time.time()
    historico = []
    for geracao in range(geracoes):
        resultados = [None] * num_workers
        erros = {}
        threads = [
            threading.Thread(target=comunicar_worker,
                             args=(w, conexoes[w], grade, faixas[w],
                                   limiar_convencimento, resultados, erros))
            for w in range(num_workers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if erros:
            print(f"[MASTER] erros na geracao {geracao+1}: {erros}")
            break

        # remonta a nova matriz global a partir das faixas devolvidas
        nova = [linha[:] for linha in grade]
        for w in range(num_workers):
            ini, fim = faixas[w]
            for offset, idx_linha in enumerate(range(ini, fim)):
                nova[idx_linha] = resultados[w][offset]
        grade = nova

        c = contar_estados(grade)
        historico.append(c)
        if verbose:
            print(f"Geracao {geracao+1:03d} | Ignorantes: {c[IGNORANTE]:>10,} | "
                  f"Espalhadores: {c[ESPALHADOR]:>10,} | Inativos: {c[INATIVO]:>10,}")
        if c[ESPALHADOR] == 0:
            if verbose:
                print("\nPropagacao encerrada: nao ha mais espalhadores.")
            break

    tempo = time.time() - inicio

    # encerra os workers
    for conn in conexoes:
        try:
            enviar_msg(conn, {"tipo": "fim"})
            conn.close()
        except Exception:  # noqa
            pass
    servidor.close()

    if verbose:
        total = linhas * colunas
        f = contar_estados(grade)
        print("\n=== RESULTADO FINAL ===")
        print(f"Tempo total: {tempo:.4f} s")
        print(f"Ignorantes:  {f[IGNORANTE]:,} ({f[IGNORANTE]/total*100:.2f}%)")
        print(f"Espalhadores:{f[ESPALHADOR]:,} ({f[ESPALHADOR]/total*100:.2f}%)")
        print(f"Inativos:    {f[INATIVO]:,} ({f[INATIVO]/total*100:.2f}%)")

    return grade, tempo, historico


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Master distribuido de fake news")
    p.add_argument("--linhas", type=int, default=100)
    p.add_argument("--colunas", type=int, default=100)
    p.add_argument("--geracoes", type=int, default=50)
    p.add_argument("--espalhadores", type=float, default=0.05)
    p.add_argument("--limiar", type=int, default=3)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=9099)
    args = p.parse_args()
    executar_simulacao(args.linhas, args.colunas, args.geracoes,
                       args.espalhadores, args.limiar, args.workers,
                       args.host, args.porta)

"""
benchmark.py
============
Mede e compara o desempenho das versoes sequencial, paralela (threads) e
distribuida (sockets/processos), variando:
  - tamanho da grade
  - percentual inicial de espalhadores
  - numero de threads (paralela)
  - numero de workers/processos (distribuida)

Metricas:
  - speedup    S(p) = T_sequencial / T_paralelo
  - eficiencia E(p) = S(p) / p

Saida: resultados/benchmark.csv

IMPORTANTE: rode este script na MAQUINA DE TESTE do grupo (multi-core).
Os numeros dependem diretamente do numero de nucleos fisicos disponiveis.

Uso:
    python benchmark.py                  # configuracao padrao (rapida)
    python benchmark.py --completo       # varredura maior (mais demorada)
"""

import csv
import time
import argparse
import os
import sys

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    sys.path.insert(0, os.path.join(_RAIZ, _p))

import FakeNews_sequencial as seq
import FakeNews_paralelo as par
from runner_distribuido import rodar_distribuido

# Saidas ficam na RAIZ do projeto (um nivel acima de codigo/).
RESULTADOS = os.path.join(_RAIZ, "..", "resultados")
os.makedirs(RESULTADOS, exist_ok=True)
CSV_PATH = os.path.join(RESULTADOS, "benchmark.csv")


def medir(funcao, repeticoes=1):
    """Roda 'funcao' e retorna o MENOR tempo (menos ruido do SO)."""
    melhor = float("inf")
    for _ in range(repeticoes):
        t = funcao()
        melhor = min(melhor, t)
    return melhor


def rodar(grades, percentuais, threads_lista, workers_lista,
          geracoes, limiar, repeticoes):
    linhas_csv = []
    for (linhas, colunas) in grades:
        for perc in percentuais:
            cfg = f"{linhas}x{colunas} | {perc*100:.0f}% esp"
            print(f"\n### Cenario: {cfg} | {geracoes} geracoes ###")

            # --- Sequencial (referencia) ---
            t_seq = medir(lambda: seq.executar_simulacao(
                linhas, colunas, geracoes, perc, limiar, verbose=False)[1], repeticoes)
            print(f"  Sequencial         : {t_seq:.4f} s")
            linhas_csv.append(["sequencial", linhas, colunas, geracoes, perc,
                               1, round(t_seq, 5), 1.0, 1.0])

            # --- Paralela (threads) ---
            for nt in threads_lista:
                t_par = medir(lambda nt=nt: par.executar_simulacao(
                    linhas, colunas, geracoes, perc, limiar,
                    num_threads=nt, verbose=False)[1], repeticoes)
                s = t_seq / t_par if t_par > 0 else 0
                e = s / nt
                print(f"  Paralela  ({nt:>2} thr) : {t_par:.4f} s | "
                      f"speedup {s:.2f} | efic {e:.2f}")
                linhas_csv.append(["paralela", linhas, colunas, geracoes, perc,
                                   nt, round(t_par, 5), round(s, 4), round(e, 4)])

            # --- Distribuida (workers) ---
            for nw in workers_lista:
                t_dist = medir(lambda nw=nw: rodar_distribuido(
                    linhas, colunas, geracoes, perc, limiar,
                    num_workers=nw)[1], repeticoes)
                s = t_seq / t_dist if t_dist > 0 else 0
                e = s / nw
                print(f"  Distrib.  ({nw:>2} wrk) : {t_dist:.4f} s | "
                      f"speedup {s:.2f} | efic {e:.2f}")
                linhas_csv.append(["distribuida", linhas, colunas, geracoes, perc,
                                   nw, round(t_dist, 5), round(s, 4), round(e, 4)])

    return linhas_csv


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--completo", action="store_true",
                   help="varredura maior (mais demorada)")
    p.add_argument("--repeticoes", type=int, default=1)
    args = p.parse_args()

    if args.completo:
        grades = [(100, 100), (200, 200), (300, 300)]
        percentuais = [0.02, 0.05, 0.10]
        threads_lista = [1, 2, 4, 8]
        workers_lista = [1, 2, 4]
        geracoes = 50
    else:
        grades = [(100, 100), (150, 150)]
        percentuais = [0.02, 0.05]
        threads_lista = [1, 2, 4]
        workers_lista = [1, 2, 4]
        geracoes = 30

    print("=" * 60)
    print("BENCHMARK: sequencial x paralela x distribuida")
    print(f"Nucleos logicos disponiveis: {os.cpu_count()}")
    print("=" * 60)

    inicio = time.time()
    linhas_csv = rodar(grades, percentuais, threads_lista, workers_lista,
                       geracoes, limiar=3, repeticoes=args.repeticoes)

    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["versao", "linhas", "colunas", "geracoes",
                    "perc_espalhadores", "unidades", "tempo_s",
                    "speedup", "eficiencia"])
        w.writerows(linhas_csv)

    print(f"\nConcluido em {time.time()-inicio:.1f} s")
    print(f"CSV salvo em: {os.path.abspath(CSV_PATH)}")


if __name__ == "__main__":
    main()

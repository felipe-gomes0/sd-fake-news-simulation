"""
testar_corretude.py
===================
Verifica que as versoes SEQUENCIAL, PARALELA e DISTRIBUIDA produzem
EXATAMENTE o mesmo resultado (mesma grade final e mesmo historico),
para varias configuracoes. Se passar, as versoes paralela/distribuida
preservam o comportamento logico da sequencial (requisito do trabalho).
"""

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

import FakeNews_sequencial as seq
import FakeNews_paralelo as par
from runner_distribuido import rodar_distribuido


def comparar(cfg):
    linhas, colunas, geracoes, perc, limiar = cfg

    g_seq, _, h_seq = seq.executar_simulacao(
        linhas, colunas, geracoes, perc, limiar, verbose=False)

    ok_par = True
    for nt in (1, 2, 4, 8):
        g_par, _, h_par = par.executar_simulacao(
            linhas, colunas, geracoes, perc, limiar, num_threads=nt, verbose=False)
        if g_par != g_seq or h_par != h_seq:
            ok_par = False
            print(f"    [FALHA] paralelo com {nt} threads divergiu")

    ok_dist = True
    for nw in (1, 2, 3):
        g_d, _, h_d = rodar_distribuido(
            linhas, colunas, geracoes, perc, limiar, num_workers=nw)
        if g_d != g_seq or h_d != h_seq:
            ok_dist = False
            print(f"    [FALHA] distribuido com {nw} workers divergiu")

    status = "OK" if (ok_par and ok_dist) else "FALHOU"
    print(f"  Grade {linhas}x{colunas}, {geracoes} ger, {perc*100:.0f}% esp, "
          f"limiar {limiar}: paralelo={'OK' if ok_par else 'X'} "
          f"distribuido={'OK' if ok_dist else 'X'} -> {status}")
    return ok_par and ok_dist


if __name__ == "__main__":
    print("=== TESTE DE CORRETUDE (sequencial == paralela == distribuida) ===\n")
    configs = [
        (30, 30, 20, 0.05, 3),
        (50, 40, 25, 0.02, 2),
        (47, 53, 15, 0.10, 3),   # dimensoes nao multiplas do nº de workers
        (100, 100, 30, 0.05, 3),
    ]
    todos_ok = all(comparar(c) for c in configs)
    print("\n" + ("TODOS OS TESTES PASSARAM ✓" if todos_ok
                  else "HOUVE FALHAS ✗"))
